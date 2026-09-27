# Xəzər TV EPG

Bu repo `https://xezer.tvstream.az/schedule.csv` faylını avtomatik oxuyub
XMLTV formatında `xezer.xml` yaradır.

## Playlist üçün

M3U kanal sətrində:

```m3u
#EXTINF:-1 tvg-id="XezerTV.az" tvg-name="Xəzər TV" group-title="Azərbaycan",Xəzər TV
KANAL_LINKI
```

EPG URL kimi GitHub Raw linkini istifadə edin:

```text
https://raw.githubusercontent.com/SIZIN_ISTIFADECI_ADINIZ/SIZIN_REPO_ADINIZ/main/xezer.xml
```

və ya playlist başında:

```m3u
#EXTM3U x-tvg-url="https://raw.githubusercontent.com/SIZIN_ISTIFADECI_ADINIZ/SIZIN_REPO_ADINIZ/main/xezer.xml"
```

## GitHub Actions

`.github/workflows/xezer-epg.yml` hər 6 saatdan bir `xezer.xml` faylını yeniləyir.
İlk dəfə `Actions` bölməsində `Xəzər TV EPG` workflow-u `Run workflow` ilə əl ilə də işə sala bilərsiniz.

Əgər `git push` icazə xətası versə:
`Settings -> Actions -> General -> Workflow permissions -> Read and write permissions`.
