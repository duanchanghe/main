import 'dart:async';
import 'package:just_audio/just_audio.dart';
import 'package:audio_session/audio_session.dart';

class AudioService {
  final AudioPlayer _player = AudioPlayer();
  final _bufferingController = StreamController<bool>.broadcast();
  final _bufferedController = StreamController<Duration>.broadcast();

  Stream<bool> get bufferingStream => _bufferingController.stream;
  Stream<Duration> get bufferedStream => _bufferedController.stream;

  AudioPlayer get player => _player;

  Stream<Duration> get positionStream => _player.positionStream;
  Stream<Duration?> get durationStream => _player.durationStream;
  Stream<PlayerState> get playerStateStream => _player.playerStateStream;
  Stream<bool> get playingStream => _player.playingStream;

  Duration get position => _player.position;
  Duration? get duration => _player.duration;
  bool get isPlaying => _player.playing;

  AudioService() {
    _setupSession();
    _setupBufferingListener();
  }

  Future<void> _setupSession() async {
    try {
      final session = await AudioSession.instance;
      await session.configure(const AudioSessionConfiguration.speech());

      session.interruptionEventStream.listen((event) {
        if (event.begin) {
          switch (event.type) {
            case AudioInterruptionType.duck:
              _player.setVolume(0.5);
              break;
            case AudioInterruptionType.pause:
            case AudioInterruptionType.unknown:
              _player.pause();
              break;
          }
        } else {
          switch (event.type) {
            case AudioInterruptionType.duck:
              _player.setVolume(1.0);
              break;
            case AudioInterruptionType.pause:
              _player.play();
              break;
            case AudioInterruptionType.unknown:
              break;
          }
        }
      });

      session.becomingNoisyEventStream.listen((_) {
        _player.pause();
      });
    } catch (e) {
      print('Audio session setup failed: $e');
    }
  }

  void _setupBufferingListener() {
    _player.playerStateStream.listen((state) {
      _bufferingController.add(state.processingState == ProcessingState.buffering);
    });
  }

  Future<void> setUrl(String url) async {
    try {
      final fullUrl = url.startsWith('http') ? url : 'http://localhost:8000$url';

      await _player.setUrl(fullUrl);

      _player.positionStream.listen((pos) {
        _updateBufferedPosition();
      });
    } catch (e) {
      print('Failed to set URL: $e');
      rethrow;
    }
  }

  Future<void> _updateBufferedPosition() async {
    try {
      final buffered = _player.bufferedPosition;
      _bufferedController.add(buffered);
    } catch (e) {
      print('Failed to get buffered position: $e');
    }
  }

  Future<void> play() async {
    await _player.play();
  }

  Future<void> pause() async {
    await _player.pause();
  }

  Future<void> stop() async {
    await _player.stop();
  }

  Future<void> seek(Duration position) async {
    await _player.seek(position);
  }

  Future<void> setSpeed(double speed) async {
    await _player.setSpeed(speed.clamp(0.5, 2.0));
  }

  Future<void> setVolume(double volume) async {
    await _player.setVolume(volume.clamp(0.0, 1.0));
  }

  Future<Duration?> get bufferedPosition async {
    return _player.bufferedPosition;
  }

  Future<void> setLoopMode(LoopMode mode) async {
    await _player.setLoopMode(mode);
  }

  Future<void> setShuffleMode(bool enabled) async {
    await _player.setShuffleModeEnabled(enabled);
  }

  void dispose() {
    _bufferingController.close();
    _bufferedController.close();
    _player.dispose();
  }
}
