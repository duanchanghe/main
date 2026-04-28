"""
精品有声书 API 视图
支持按章节生成、MinIO 存储
"""
import os
import threading
import logging
from datetime import datetime
from django.conf import settings
from django.http import FileResponse, HttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from .serializers import (
    UserSerializer, NovelSerializer, CharacterSerializer,
    SceneSerializer, DialogueSerializer, ChapterAudioSerializer
)
from novels.models import Novel, Character, Scene, Dialogue, AudioJob, AudioSegment
from services.audiobook_producer import AudioBookProducer, get_audiobook_producer
from services.storage import storage, MinIOStorageError

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    from django.contrib.auth import authenticate
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    if user:
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        })
    return Response({'error': '用户名或密码错误'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    return Response(UserSerializer(request.user).data)


class NovelViewSet(viewsets.ModelViewSet):
    """小说管理视图集"""
    serializer_class = NovelSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    # 分页
    pagination_class = None  # 可按需启用

    def get_queryset(self):
        return Novel.objects.filter(uploaded_by=self.request.user).select_related('uploaded_by')

    def perform_create(self, serializer):
        """上传小说时自动提取内容"""
        novel = serializer.save(uploaded_by=self.request.user)
        self._extract_content_async(novel)

    def _extract_content_async(self, novel):
        """异步提取小说内容 - 增强错误处理"""
        def process():
            from django.db import transaction
            try:
                if novel.file_path:
                    file_path = novel.file_path.path
                    if os.path.exists(file_path):
                        # 检测编码
                        encoding_hint = getattr(novel, '_encoding_hint', None)
                        encoding = encoding_hint or 'utf-8'

                        with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                            content = f.read()

                        # 清理内容
                        content = content.strip()
                        if content:
                            with transaction.atomic():
                                novel.content = content
                                novel.status = 'pending'
                                novel.save(update_fields=['content', 'status'])
                        else:
                            novel.status = 'failed'
                            novel.save(update_fields=['status'])
            except UnicodeDecodeError:
                logger.error(f"文件编码不支持: {novel.file_path.path}")
                novel.status = 'failed'
                novel.save(update_fields=['status'])
            except Exception as e:
                logger.error(f"提取小说内容失败: {e}")
                novel.status = 'failed'
                novel.save(update_fields=['status'])

        thread = threading.Thread(target=process)
        thread.daemon = True
        thread.start()

    @action(detail=True, methods=['post'])
    def analyze(self, request, pk=None):
        """AI 分析小说"""
        novel = self.get_object()

        if not novel.content:
            return Response({'error': '小说内容为空'}, status=status.HTTP_400_BAD_REQUEST)

        if novel.status == 'analyzing':
            return Response({'error': '正在分析中，请稍候'}, status=status.HTTP_400_BAD_REQUEST)

        if novel.status == 'completed':
            return Response({
                'status': 'completed',
                'message': '分析已完成',
                'data': {
                    'characters_count': novel.characters.count(),
                    'scenes_count': novel.scenes.count()
                }
            })

        from django.db import transaction

        with transaction.atomic():
            novel.status = 'analyzing'
            novel.save(update_fields=['status'])

        def analyze_thread():
            from django.db import transaction
            try:
                producer = get_audiobook_producer()
                analysis_result = producer.analyze_novel(novel.content)

                with transaction.atomic():
                    producer.save_analysis(novel, analysis_result)
                    novel.refresh_from_db()
                    novel.status = 'completed'
                    novel.save(update_fields=['status', 'ai_analysis', 'genre', 'setting', 'analysis_completed_at'])

            except Exception as e:
                logger.exception(f"分析失败: {novel.id}")
                with transaction.atomic():
                    novel.refresh_from_db()
                    novel.status = 'failed'
                    novel.save(update_fields=['status'])

        thread = threading.Thread(target=analyze_thread)
        thread.daemon = True
        thread.start()

        return Response({
            'status': 'analyzing',
            'message': 'AI 分析已启动'
        })

    @action(detail=True, methods=['post'])
    def generate_chapter(self, request, pk=None):
        """生成单个章节音频"""
        novel = self.get_object()
        chapter_number = request.data.get('chapter_number', 1)

        use_multi_voice = request.data.get('multi_voice', True)
        use_bgm = request.data.get('bgm', True)
        use_sfx = request.data.get('sfx', True)

        # 检查章节是否存在
        if not novel.scenes.filter(chapter_number=int(chapter_number)).exists():
            return Response(
                {'error': f'章节 {chapter_number} 不存在，请先分析小说'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 检查是否有正在进行的任务
        existing_job = AudioJob.objects.filter(
            novel=novel,
            status__in=['queued', 'analyzing', 'generating', 'saving', 'merging']
        ).first()

        if existing_job:
            return Response({
                'error': '已有进行中的任务',
                'job_id': existing_job.id
            }, status=status.HTTP_400_BAD_REQUEST)

        def generate_thread():
            from django.db import transaction
            try:
                producer = get_audiobook_producer()
                output_dir = settings.MEDIA_ROOT / 'audiobooks' / f'novel_{novel.id}'
                os.makedirs(output_dir, exist_ok=True)

                chapter_audio = producer.generate_chapter_audio(
                    novel=novel,
                    chapter_number=int(chapter_number),
                    output_dir=str(output_dir),
                    use_multi_voice=use_multi_voice,
                    use_bgm=use_bgm,
                    use_sfx=use_sfx
                )

                with transaction.atomic():
                    AudioJob.objects.create(
                        novel=novel,
                        user=request.user,
                        status='completed' if chapter_audio.status == 'completed' else 'failed',
                        output_path=chapter_audio.minio_path or chapter_audio.output_path,
                        error_message=chapter_audio.error_message,
                        completed_at=datetime.now()
                    )

            except Exception as e:
                logger.exception(f"章节生成失败: {novel.id} chapter={chapter_number}")
                with transaction.atomic():
                    AudioJob.objects.create(
                        novel=novel,
                        user=request.user,
                        status='failed',
                        error_message=str(e),
                        completed_at=datetime.now()
                    )

        thread = threading.Thread(target=generate_thread)
        thread.daemon = True
        thread.start()

        return Response({
            'status': 'generating',
            'chapter_number': chapter_number,
            'message': f'第{chapter_number}章生成已启动'
        })

    @action(detail=True, methods=['post'])
    def generate_all(self, request, pk=None):
        """生成全部章节音频"""
        novel = self.get_object()

        # 检查分析是否完成
        if not novel.ai_analysis:
            return Response({
                'error': '请先完成AI分析'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 检查是否有正在进行的任务
        existing_job = AudioJob.objects.filter(
            novel=novel,
            status__in=['queued', 'analyzing', 'generating', 'saving', 'merging']
        ).first()

        if existing_job:
            return Response({
                'error': '已有进行中的任务',
                'job_id': existing_job.id
            }, status=status.HTTP_400_BAD_REQUEST)

        use_multi_voice = request.data.get('multi_voice', True)
        use_bgm = request.data.get('bgm', True)
        use_sfx = request.data.get('sfx', True)

        from django.db import transaction

        with transaction.atomic():
            job = AudioJob.objects.create(
                novel=novel,
                user=request.user,
                status='queued',
                use_multi_voice=use_multi_voice,
                use_bgm=use_bgm,
                use_sfx=use_sfx,
                total_scenes=novel.scenes.count()
            )

        def generate_thread():
            from django.db import transaction
            import traceback
            try:
                with transaction.atomic():
                    job.status = 'generating'
                    job.started_at = datetime.now()
                    job.save()

                producer = get_audiobook_producer()
                output_dir = settings.MEDIA_ROOT / 'audiobooks' / f'job_{job.id}'
                os.makedirs(output_dir, exist_ok=True)

                def progress_callback(progress, step):
                    try:
                        job.progress = progress
                        job.current_step = step
                        job.save(update_fields=['progress', 'current_step'])
                    except Exception:
                        pass  # 忽略保存错误

                result = producer.generate_full_audiobook(
                    novel=novel,
                    output_dir=str(output_dir),
                    use_multi_voice=use_multi_voice,
                    use_bgm=use_bgm,
                    use_sfx=use_sfx,
                    progress_callback=progress_callback
                )

                with transaction.atomic():
                    job.status = 'completed'
                    job.progress = 100
                    job.output_path = result.get('full_audiobook_minio', result.get('full_audiobook_path', ''))
                    job.completed_at = datetime.now()
                    job.save()

            except Exception as e:
                logger.exception(f"有声书生成失败: {job.id}")
                error_detail = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
                with transaction.atomic():
                    job.status = 'failed'
                    job.error_message = error_detail[:2000]  # 限制错误信息长度
                    job.completed_at = datetime.now()
                    job.save()

        thread = threading.Thread(target=generate_thread)
        thread.daemon = True
        thread.start()

        return Response({
            'job_id': job.id,
            'status': 'queued',
            'message': '有声书生成任务已创建'
        })

    @action(detail=True, methods=['get'])
    def jobs(self, request, pk=None):
        """获取任务列表"""
        novel = self.get_object()
        jobs = AudioJob.objects.filter(novel=novel).order_by('-created_at')
        return Response([{
            'id': j.id,
            'status': j.status,
            'progress': j.progress,
            'current_step': j.current_step,
            'output_path': j.output_path,
            'error_message': j.error_message,
            'created_at': j.created_at.isoformat(),
            'completed_at': j.completed_at.isoformat() if j.completed_at else None
        } for j in jobs])

    @action(detail=True, methods=['get'])
    def chapters(self, request, pk=None):
        """获取章节列表"""
        novel = self.get_object()
        chapters = novel.scenes.values('chapter_number').distinct().order_by('chapter_number')
        return Response([{
            'chapter_number': c['chapter_number'],
            'scenes_count': novel.scenes.filter(chapter_number=c['chapter_number']).count()
        } for c in chapters])

    @action(detail=True, methods=['get'])
    def scenes(self, request, pk=None):
        """获取场景列表"""
        novel = self.get_object()
        chapter_number = request.query_params.get('chapter')

        scenes = novel.scenes.all()
        if chapter_number:
            scenes = scenes.filter(chapter_number=int(chapter_number))

        scenes = scenes.order_by('chapter_number', 'scene_id')
        return Response([{
            'id': s.id,
            'chapter_number': s.chapter_number,
            'scene_id': s.scene_id,
            'location': s.location,
            'time_of_day': s.time_of_day,
            'mood': s.mood,
            'suggested_bgm': s.suggested_bgm,
            'dialogues_count': s.dialogues.count()
        } for s in scenes])

    @action(detail=True, methods=['get'])
    def characters(self, request, pk=None):
        """获取角色列表"""
        novel = self.get_object()
        characters = novel.characters.all()
        return Response([{
            'id': c.id,
            'name': c.name,
            'role_type': c.role_type,
            'gender': c.gender,
            'voice_id': c.voice_id,
            'importance_score': c.importance_score
        } for c in characters])

    @action(detail=True, methods=['put'])
    def update_character(self, request, pk=None):
        """更新角色配置"""
        novel = self.get_object()
        char_id = request.data.get('character_id')
        voice_id = request.data.get('voice_id')

        try:
            char = novel.characters.get(id=char_id)
            if voice_id:
                char.voice_id = voice_id
            char.save()
            return Response({'message': '更新成功'})
        except Character.DoesNotExist:
            return Response({'error': '角色不存在'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['delete'])
    def delete_novel(self, request, pk=None):
        """删除小说及其关联资源"""
        import shutil
        novel = self.get_object()

        # 清理关联的音频文件
        try:
            audio_dirs = [
                settings.MEDIA_ROOT / 'audiobooks' / f'novel_{novel.id}',
            ]

            for audio_dir in audio_dirs:
                if audio_dir.exists():
                    shutil.rmtree(audio_dir)
                    logger.info(f"已清理小说音频目录: {audio_dir}")

        except Exception as e:
            logger.warning(f"清理小说文件失败: {e}")

        # 清理数据库记录（CASCADE 会自动删除关联数据）
        novel.delete()

        return Response({'message': '小说已删除'})

    @action(detail=True, methods=['get'])
    def analysis_result(self, request, pk=None):
        """获取分析结果"""
        novel = self.get_object()
        if not novel.ai_analysis:
            return Response({'error': '尚未分析'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'novel_info': novel.ai_analysis.get('novel_info', {}),
            'characters_count': novel.characters.count(),
            'scenes_count': novel.scenes.count(),
            'chapters_count': novel.scenes.values('chapter_number').distinct().count()
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_job_status(request, job_id):
    """获取任务状态"""
    try:
        job = AudioJob.objects.get(id=job_id, user=request.user)
        return Response({
            'id': job.id,
            'novel_id': job.novel_id,
            'status': job.status,
            'progress': job.progress,
            'current_step': job.current_step,
            'output_path': job.output_path,
            'error_message': job.error_message,
            'created_at': job.created_at.isoformat(),
            'started_at': job.started_at.isoformat() if job.started_at else None,
            'completed_at': job.completed_at.isoformat() if job.completed_at else None
        })
    except AudioJob.DoesNotExist:
        return Response({'error': '任务不存在'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_job(request, job_id):
    """取消任务"""
    try:
        job = AudioJob.objects.get(id=job_id, user=request.user)
        if job.status in ('completed', 'failed', 'cancelled'):
            return Response({'error': '任务无法取消'}, status=status.HTTP_400_BAD_REQUEST)

        job.status = 'cancelled'
        job.save()
        return Response({'message': '任务已取消'})
    except AudioJob.DoesNotExist:
        return Response({'error': '任务不存在'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_audio_url(request, job_id):
    """获取音频 URL（支持预签名 URL）"""
    try:
        job = AudioJob.objects.select_related('novel').get(id=job_id)
        if job.status != 'completed':
            return Response({'error': '音频未就绪'}, status=status.HTTP_400_BAD_REQUEST)

        if job.output_path:
            if job.output_path.startswith('http'):
                return Response({'url': job.output_path})
            else:
                url = storage.get_presigned_url(
                    job.output_path.replace(f'{job.novel.id}/', ''),
                    bucket_name='chapters'
                )
                return Response({'url': url})

        return Response({'error': '无音频文件'}, status=status.HTTP_404_NOT_FOUND)
    except AudioJob.DoesNotExist:
        return Response({'error': '任务不存在'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([AllowAny])
def stream_audio(request, job_id):
    """流式播放音频"""
    try:
        job = AudioJob.objects.select_related('novel').get(id=job_id)
        if job.status != 'completed':
            return Response({'error': '音频未就绪'}, status=status.HTTP_404_NOT_FOUND)

        if job.output_path:
            # 尝试多个可能的路径
            possible_paths = [
                settings.MEDIA_ROOT / 'audiobooks' / 'job_' + str(job.id) / 'full_audiobook.mp3',
                settings.MEDIA_ROOT / 'audiobooks' / f'novel_{job.novel.id}' / 'full_audiobook.mp3',
                settings.MEDIA_ROOT / job.output_path.lstrip('/'),
            ]

            audio_file = None
            for path in possible_paths:
                if path.exists():
                    audio_file = path
                    break

            if audio_file:
                response = FileResponse(
                    open(audio_file, 'rb'),
                    content_type='audio/mpeg'
                )
                response['Content-Disposition'] = f'inline; filename="audiobook_{job.novel.title}.mp3"'
                return response

        return Response({'error': '文件不存在'}, status=status.HTTP_404_NOT_FOUND)
    except AudioJob.DoesNotExist:
        return Response({'error': '任务不存在'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([AllowAny])
def available_voices(request):
    """获取可用音色列表"""
    from services.minimax_tts import MiniMaxTTS
    try:
        tts = MiniMaxTTS()
        return Response(tts.get_available_voices())
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['GET'])
@permission_classes([AllowAny])
def available_sfx(request):
    """获取可用音效列表"""
    try:
        producer = get_audiobook_producer()
        if hasattr(producer, 'tts'):
            return Response(producer.tts.get_available_voices())
        return Response([])
    except Exception as e:
        logger.error(f"获取音效列表失败: {e}")
        return Response({'error': '服务暂时不可用'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_upload_url(request):
    """获取预签名上传 URL（用于客户端直接上传到 MinIO）"""
    filename = request.data.get('filename')
    content_type = request.data.get('content_type', 'application/octet-stream')

    if not filename:
        return Response({'error': '缺少文件名'}, status=status.HTTP_400_BAD_REQUEST)

    import uuid
    object_name = f"uploads/{request.user.id}/{uuid.uuid4().hex}/{filename}"

    try:
        url = storage.get_presigned_put_url(object_name, bucket_name='uploads')
        return Response({
            'upload_url': url,
            'object_name': object_name
        })
    except MinIOStorageError as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_jobs(request):
    """获取当前用户的所有任务 - 支持分页"""
    page = int(request.query_params.get('page', 1))
    page_size = min(int(request.query_params.get('page_size', 20)), 100)

    jobs_query = AudioJob.objects.filter(user=request.user).select_related('novel').order_by('-created_at')

    total = jobs_query.count()
    start = (page - 1) * page_size
    end = start + page_size
    jobs = jobs_query[start:end]

    return Response({
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': (total + page_size - 1) // page_size,
        'results': [{
            'id': j.id,
            'novel_id': j.novel_id,
            'novel_title': j.novel.title,
            'status': j.status,
            'progress': j.progress,
            'output_path': j.output_path,
            'error_message': j.error_message,
            'created_at': j.created_at.isoformat(),
            'completed_at': j.completed_at.isoformat() if j.completed_at else None
        } for j in jobs]
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_novels(request):
    """获取当前用户的所有小说 - 支持分页"""
    page = int(request.query_params.get('page', 1))
    page_size = min(int(request.query_params.get('page_size', 20)), 100)

    novels_query = Novel.objects.filter(uploaded_by=request.user).order_by('-created_at')

    total = novels_query.count()
    start = (page - 1) * page_size
    end = start + page_size
    novels = novels_query[start:end]

    return Response({
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': (total + page_size - 1) // page_size,
        'results': [{
            'id': n.id,
            'title': n.title,
            'author': n.author,
            'genre': n.genre,
            'status': n.status,
            'characters_count': n.characters.count(),
            'scenes_count': n.scenes.count(),
            'created_at': n.created_at.isoformat(),
        } for n in novels]
    })


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_job(request, job_id):
    """删除任务及关联的临时文件"""
    try:
        job = AudioJob.objects.get(id=job_id, user=request.user)

        # 清理临时文件
        if job.output_path:
            try:
                import shutil
                # 尝试清理 job 目录
                job_dir = settings.MEDIA_ROOT / 'audiobooks' / f'job_{job.id}'
                if job_dir.exists():
                    shutil.rmtree(job_dir)
                    logger.info(f"已清理任务目录: {job_dir}")
            except Exception as e:
                logger.warning(f"清理任务文件失败: {e}")

        job.delete()
        return Response({'message': '任务已删除'})

    except AudioJob.DoesNotExist:
        return Response({'error': '任务不存在'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([AllowAny])
def available_bgm_presets(request):
    """获取可用的 BGM 预设列表"""
    from services.minimax_music import MiniMaxMusicLibrary
    library = MiniMaxMusicLibrary()
    presets = library.get_all_presets()
    return Response(presets)


@api_view(['GET'])
@permission_classes([AllowAny])
def audio_quality_check(request):
    """检查音频质量"""
    audio_path = request.query_params.get('path')

    if not audio_path:
        return Response({'error': '缺少音频路径'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        from services.audiobook_producer import AudioQualityChecker
        from pathlib import Path

        if audio_path.startswith('http'):
            return Response({'error': '暂不支持远程文件检查'}, status=status.HTTP_400_BAD_REQUEST)

        full_path = Path(settings.MEDIA_ROOT) / audio_path
        if not full_path.exists():
            return Response({'error': '文件不存在'}, status=status.HTTP_404_NOT_FOUND)

        result = AudioQualityChecker.check_audio_quality(str(full_path))
        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def tts_voices_info(request):
    """获取 TTS 音色详细信息"""
    from services.minimax_tts import MiniMaxTTS

    tts = MiniMaxTTS()
    voices = tts.VOICE_OPTIONS
    emotions = tts.EMOTION_OPTIONS

    voice_info = []
    for voice_id, desc in voices.items():
        gender = 'male' if '男' in desc or 'Male' in voice_id else 'female'
        if '旁白' in desc:
            gender = 'narrator'
        voice_info.append({
            'id': voice_id,
            'name': desc,
            'gender': gender
        })

    emotion_info = []
    for emotion in emotions:
        pitch = tts.EMOTION_PITCH_ADJUSTMENTS.get(emotion, 0)
        speed = tts.EMOTION_SPEED_ADJUSTMENTS.get(emotion, 1.0)
        emotion_info.append({
            'id': emotion,
            'pitch_adjustment': pitch,
            'speed_adjustment': speed
        })

    return Response({
        'voices': voice_info,
        'emotions': emotion_info
    })
