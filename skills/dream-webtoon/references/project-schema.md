# project.json

프로젝트 폴더 하나가 웹툰 한 편이다.

```
<사람>/
├── project.json   모든 설계와 결과
├── interview.md   인터뷰 기록 (본인 말 그대로)
├── consent.md     알린 것, 받은 동의, 뺄 내용, 비밀 범위
├── photo/         받은 사진 (공유하지 않는다)
├── art/           시트와 컷 그림 (jpg, 긴 변 1100px)
└── site/          만들어진 페이지
```

| 칸 | 뜻 |
|---|---|
| `title` · `subtitle` | 제목과 부제. 제목에 `: ` 이 있으면 그 뒤에서 줄을 바꾼다 |
| `palette` | `bg` · `pale` · `deep` · `ink`. 본인이 고른 색에서 만든다 |
| `site_url` | 배포 주소. 미리보기 이미지에 쓴다 |
| `price_per_image` | 그림 한 장 크레딧 |
| `stages` | `{name, status: done·doing·waiting, note}` 보드의 진행 단계 |
| `ask` | 보드 맨 아래 부탁 문장 |
| `pledge` · `question` | 웹툰 끝의 약속 `{label, text}` 과 독자에게 묻는 말 |
| `interview` | 메이킹북에 실을 `{q, a}`. `a` 는 본인 말 그대로 |
| `characters` | `{image, caption}` 캐릭터 시트 |
| `retakes` | `{title, before, after}` 다시 그린 전후 |
| `credits` | `{stage, what, credits}` 실제로 쓴 크레딧 |
| `cost_notes` | 비용 표 아래 설명 문장. 잔액 대조, 재지 못한 비용 |
| `lessons` | 시행착오 문장 |
| `making_intro` | 메이킹북 첫 문장 |
| `cuts` | 아래 컷 목록 |

## cuts 한 칸

| 칸 | 뜻 |
|---|---|
| `no` | 1부터 이어지는 번호 |
| `act` · `beat` | 막 이름, 이야기 단계 |
| `scene` | 장면 한 줄 |
| `evidence` | `interview` 인터뷰에서 나온 사실, `staged` 연출 |
| `status` | `done` 그림 있음, `planned` 그릴 컷, `fix` 고칠 컷 |
| `image` · `width` · `height` | 프로젝트 폴더 기준 경로와 좌표 기준 크기. 풍선 좌표는 이 크기로 적는다. 그림과 비율이 같아야 한다 |
| `ratio` | 그릴 비율 |
| `gap_after` | `none` · `short` · `medium` · `long` · `xlong` 다음 컷까지 간격 |
| `full` | 폭 꽉 채움 |
| `people` | 사람이 없는 컷이면 `false` |
| `avoid` | 얼굴 자리 `[[x, y, 폭, 높이], ...]` |
| `notes` | 해설 `{text, place}`. `place` 는 `"out"` 또는 `{left, top, right, bottom, width}` 퍼센트 |
| `balloons` | 풍선 목록 |
| `planned_text` | 아직 안 그린 컷의 글. 보드에 보인다 |

말 풍선: `{type: "talk", cx, cy, rx, ry, tip: [x, y], lines: [...], size}`
속마음: `{type: "think", cx, cy, rx, ry, dots: [[x, y, r], ...], lines: [...], size}`
