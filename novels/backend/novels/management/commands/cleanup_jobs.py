"""
清理过期任务和临时文件的管理命令
"""
import os
import shutil
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.conf import settings
from novels.models import AudioJob


class Command(BaseCommand):
    help = '清理过期的音频任务和临时文件'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='清理多少天前的任务 (默认: 7天)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅显示要清理的内容，不实际删除'
        )
        parser.add_argument(
            '--clean-temp',
            action='store_true',
            help='同时清理临时目录'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        clean_temp = options['clean_temp']

        cutoff_date = datetime.now() - timedelta(days=days)

        self.stdout.write(f"{'='*60}")
        self.stdout.write(f"清理任务开始 (清理 {days} 天前的任务)")
        if dry_run:
            self.stdout.write(self.style.WARNING("[DRY RUN] 不会实际删除任何文件"))
        self.stdout.write(f"{'='*60}\n")

        # 1. 清理过期的失败/完成任务
        old_jobs = AudioJob.objects.filter(
            completed_at__lt=cutoff_date,
            status__in=['completed', 'failed', 'cancelled']
        )

        job_count = old_jobs.count()
        self.stdout.write(f"找到 {job_count} 个过期任务")

        if dry_run:
            for job in old_jobs[:10]:
                self.stdout.write(f"  - Job #{job.id}: {job.novel.title} ({job.status})")
            if job_count > 10:
                self.stdout.write(f"  ... 还有 {job_count - 10} 个")
        else:
            # 清理关联文件
            cleaned_dirs = 0
            for job in old_jobs:
                if job.output_path:
                    job_dir = settings.MEDIA_ROOT / 'audiobooks' / f'job_{job.id}'
                    if job_dir.exists():
                        shutil.rmtree(job_dir)
                        cleaned_dirs += 1

            old_jobs.delete()
            self.stdout.write(self.style.SUCCESS(f"已删除 {job_count} 个过期任务"))
            self.stdout.write(f"已清理 {cleaned_dirs} 个任务目录")

        # 2. 清理孤立的任务目录
        audiobooks_dir = settings.MEDIA_ROOT / 'audiobooks'
        if audiobooks_dir.exists():
            orphaned = 0
            for item in audiobooks_dir.iterdir():
                if item.is_dir() and item.name.startswith('job_'):
                    job_id = int(item.name.replace('job_', ''))
                    if not AudioJob.objects.filter(id=job_id).exists():
                        orphaned += 1
                        if dry_run:
                            self.stdout.write(f"  孤立目录: {item}")
                        else:
                            shutil.rmtree(item)

            if not dry_run:
                self.stdout.write(f"已清理 {orphaned} 个孤立目录")

        # 3. 清理临时文件
        if clean_temp:
            temp_patterns = ['tmp_', 'temp_', '.tmp', '.temp']
            temp_files = 0
            temp_size = 0

            for root, dirs, files in os.walk(settings.MEDIA_ROOT):
                for f in files:
                    if any(p in f for p in temp_patterns):
                        fpath = os.path.join(root, f)
                        fsize = os.path.getsize(fpath)
                        temp_files += 1
                        temp_size += fsize

                        if not dry_run:
                            try:
                                os.remove(fpath)
                            except Exception as e:
                                self.stdout.write(self.style.WARNING(f"  删除失败: {fpath} - {e}"))

            if dry_run:
                self.stdout.write(f"临时文件: {temp_files} 个 ({temp_size / 1024 / 1024:.2f} MB)")
            else:
                self.stdout.write(self.style.SUCCESS(f"已清理 {temp_files} 个临时文件 ({temp_size / 1024 / 1024:.2f} MB)"))

        # 4. 生成统计信息
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write("当前统计:")
        self.stdout.write(f"  - 总任务数: {AudioJob.objects.count()}")
        self.stdout.write(f"  - 运行中: {AudioJob.objects.filter(status__in=['queued', 'analyzing', 'generating']).count()}")
        self.stdout.write(f"  - 已完成: {AudioJob.objects.filter(status='completed').count()}")
        self.stdout.write(f"  - 已失败: {AudioJob.objects.filter(status='failed').count()}")

        # 磁盘使用
        total_size = sum(
            f.stat().st_size
            for f in (settings.MEDIA_ROOT / 'audiobooks').rglob('*')
            if f.is_file()
        )
        self.stdout.write(f"  - 音频存储: {total_size / 1024 / 1024:.2f} MB")

        self.stdout.write(f"{'='*60}")
        self.stdout.write(self.style.SUCCESS("清理完成!"))
