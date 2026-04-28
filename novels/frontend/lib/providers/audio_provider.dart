import 'package:flutter/foundation.dart';
import '../services/audio_service.dart';
import '../models/novel.dart';

class AudioProvider with ChangeNotifier {
  final AudioService _audioService;
  Novel? _currentNovel;
  bool _isPlaying = false;
  bool _isBuffering = false;
  Duration _position = Duration.zero;
  Duration? _duration;
  Duration? _bufferedPosition;
  double _speed = 1.0;
  double _volume = 1.0;
  bool _isShuffle = false;
  bool _isRepeat = false;

  AudioProvider({AudioService? audioService})
      : _audioService = audioService ?? AudioService() {
    _setupListeners();
  }

  Novel? get currentNovel => _currentNovel;
  bool get isPlaying => _isPlaying;
  bool get isBuffering => _isBuffering;
  Duration get position => _position;
  Duration? get duration => _duration;
  Duration? get bufferedPosition => _bufferedPosition;
  double get speed => _speed;
  double get volume => _volume;
  bool get isShuffle => _isShuffle;
  bool get isRepeat => _isRepeat;

  double get progress {
    if (_duration == null || _duration!.inMilliseconds == 0) return 0;
    return _position.inMilliseconds / _duration!.inMilliseconds;
  }

  void _setupListeners() {
    _audioService.positionStream.listen((pos) {
      _position = pos;
      notifyListeners();
    });

    _audioService.durationStream.listen((dur) {
      _duration = dur;
      notifyListeners();
    });

    _audioService.playingStream.listen((playing) {
      _isPlaying = playing;
      notifyListeners();
    });

    _audioService.bufferingStream.listen((buffering) {
      _isBuffering = buffering;
      notifyListeners();
    });

    _audioService.bufferedStream.listen((buffered) {
      _bufferedPosition = buffered;
      notifyListeners();
    });
  }

  Future<void> loadAndPlay(Novel novel, String url) async {
    _currentNovel = novel;
    await _audioService.setUrl(url);
    await _audioService.play();
    notifyListeners();
  }

  Future<void> loadJob(int jobId) async {
    await _audioService.setUrl('/api/jobs/$jobId/stream/');
    await _audioService.play();
    notifyListeners();
  }

  Future<void> play() async {
    await _audioService.play();
  }

  Future<void> pause() async {
    await _audioService.pause();
  }

  Future<void> stop() async {
    await _audioService.stop();
    _currentNovel = null;
    _position = Duration.zero;
    _duration = null;
    notifyListeners();
  }

  Future<void> seek(Duration position) async {
    await _audioService.seek(position);
  }

  Future<void> seekToProgress(double progress) async {
    if (_duration != null) {
      final position = Duration(
        milliseconds: (_duration!.inMilliseconds * progress).toInt(),
      );
      await _audioService.seek(position);
    }
  }

  Future<void> setSpeed(double speed) async {
    _speed = speed;
    await _audioService.setSpeed(speed);
    notifyListeners();
  }

  Future<void> setVolume(double volume) async {
    _volume = volume.clamp(0.0, 1.0);
    await _audioService.setVolume(_volume);
    notifyListeners();
  }

  void toggleShuffle() {
    _isShuffle = !_isShuffle;
    notifyListeners();
  }

  void toggleRepeat() {
    _isRepeat = !_isRepeat;
    notifyListeners();
  }

  String formatDuration(Duration duration) {
    String twoDigits(int n) => n.toString().padLeft(2, '0');
    final hours = duration.inHours;
    final minutes = duration.inMinutes.remainder(60);
    final seconds = duration.inSeconds.remainder(60);
    if (hours > 0) {
      return '${twoDigits(hours)}:${twoDigits(minutes)}:${twoDigits(seconds)}';
    }
    return '${twoDigits(minutes)}:${twoDigits(seconds)}';
  }

  String get positionText => formatDuration(_position);
  String get durationText => _duration != null ? formatDuration(_duration!) : '--:--';

  @override
  void dispose() {
    _audioService.dispose();
    super.dispose();
  }
}
