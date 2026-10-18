import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import '../../core/api_client.dart';
import '../../core/models.dart';
import '../../core/constants.dart';
import '../../shared/theme/app_theme.dart';

class LiveHomeScreen extends StatefulWidget {
  const LiveHomeScreen({super.key});
  @override
  State<LiveHomeScreen> createState() => _State();
}

class _State extends State<LiveHomeScreen> {
  List<LiveStream> _live = [], _ended = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final r1 = await ApiClient.get('/live/', params: {'status': 'live'});
    final r2 = await ApiClient.get('/live/', params: {'status': 'ended'});
    setState(() {
      if (r1['ok'])
        _live = (r1['data'] is List ? r1['data'] : r1['data']['results'] ?? [])
            .map<LiveStream>((e) => LiveStream.fromJson(e))
            .toList();
      if (r2['ok'])
        _ended = (r2['data'] is List ? r2['data'] : r2['data']['results'] ?? [])
            .map<LiveStream>((e) => LiveStream.fromJson(e))
            .toList();
      _loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('🔴 Live Streams')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _load,
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  if (_live.isNotEmpty) ...[
                    _header('🔴 Live Now (${_live.length})'),
                    ..._live.map((s) => _StreamCard(stream: s)),
                  ] else
                    const Center(
                        child: Padding(
                            padding: EdgeInsets.all(32),
                            child: Text('No live streams right now',
                                style: TextStyle(
                                    color: AppTheme.textGrey, fontSize: 15)))),
                  if (_ended.isNotEmpty) ...[
                    const SizedBox(height: 16),
                    _header('📼 Recent Streams'),
                    ..._ended
                        .take(6)
                        .map((s) => _StreamCard(stream: s, dimmed: true)),
                  ],
                ],
              )),
    );
  }

  Widget _header(String t) => Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Text(t,
          style: const TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w800,
              color: AppTheme.textDark)));
}

class _StreamCard extends StatelessWidget {
  final LiveStream stream;
  final bool dimmed;
  const _StreamCard({required this.stream, this.dimmed = false});

  @override
  Widget build(BuildContext context) {
    return Opacity(
        opacity: dimmed ? 0.75 : 1,
        child: Container(
          margin: const EdgeInsets.only(bottom: 12),
          decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: const Color(0xFFEEF2F6))),
          child: Row(children: [
            ClipRRect(
                borderRadius:
                    const BorderRadius.horizontal(left: Radius.circular(14)),
                child: stream.thumbnailUrl != null
                    ? CachedNetworkImage(
                        imageUrl: stream.thumbnailUrl!,
                        width: 100,
                        height: 80,
                        fit: BoxFit.cover)
                    : Container(
                        width: 100,
                        height: 80,
                        decoration: const BoxDecoration(
                            gradient: LinearGradient(
                                colors: [AppTheme.primary, Color(0xFF1A4B8A)])),
                        child: const Icon(Icons.video_camera_back_outlined,
                            color: Colors.white38, size: 32))),
            Expanded(
                child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          if (stream.isLive)
                            Container(
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 7, vertical: 2),
                                decoration: BoxDecoration(
                                    color: AppTheme.secondary,
                                    borderRadius: BorderRadius.circular(20)),
                                child: const Text('● LIVE',
                                    style: TextStyle(
                                        color: Colors.white,
                                        fontSize: 10,
                                        fontWeight: FontWeight.w800))),
                          const SizedBox(height: 4),
                          Text(stream.title,
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                              style: const TextStyle(
                                  fontWeight: FontWeight.w700,
                                  fontSize: 14,
                                  color: AppTheme.textDark)),
                          const SizedBox(height: 4),
                          Text(stream.vendorName,
                              style: const TextStyle(
                                  color: AppTheme.textGrey, fontSize: 12)),
                          const SizedBox(height: 4),
                          Row(children: [
                            const Icon(Icons.remove_red_eye_outlined,
                                size: 13, color: AppTheme.textGrey),
                            const SizedBox(width: 3),
                            Text('${stream.views}',
                                style: const TextStyle(
                                    fontSize: 12, color: AppTheme.textGrey)),
                            const SizedBox(width: 10),
                            const Icon(Icons.favorite_border,
                                size: 13, color: AppTheme.textGrey),
                            const SizedBox(width: 3),
                            Text('${stream.likes}',
                                style: const TextStyle(
                                    fontSize: 12, color: AppTheme.textGrey)),
                          ]),
                        ]))),
          ]),
        ));
  }
}
