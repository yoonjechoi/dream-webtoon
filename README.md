# dream-webtoon

A Claude Code plugin that turns a warm interview about someone's dream into a vertical-scroll webtoon, a progress board, and a making-of book. The docs are in Korean.

한 사람의 꿈을 따뜻하게 인터뷰해 세로 스크롤 웹툰으로 만들고, 진행 보드와 메이킹북까지 올려 공유하는 Claude Code 플러그인입니다.

```
셀카 → 캐스팅 → 인터뷰 → 이야기 설계(짧으면 더 들려주기) → 작화 → 말풍선 → 검수 → 완성 검토(수정 3번) → 후기 · 공개 동의 → 공개
```

## 설치

```bash
claude plugin marketplace add yoonjechoi/dream-webtoon
```

```bash
claude plugin install dream-webtoon@dream-webtoon
```

## 필요한 것

- Claude Code, Python 3
- 힉스필드 연결 (그림). 유료 크레딧이 듭니다
- Vercel CLI (공개). 없으면 아티팩트로 올립니다
- iris-room 플러그인 (선택). 카톡방이나 오픈프로필 1:1에서 인터뷰할 때. 세션 두 개를 씁니다

## 쓰는 법

```
우리 동생 인터뷰해서 꿈 웹툰 만들어 줘
```

시작하기 전에 깜짝 선물인지, 누가 승인하는지, 크레딧을 얼마까지 쓸지를 묻습니다.

## 들어 있는 것

| 스킬 | 하는 일 |
|---|---|
| `dream-webtoon` | 전체 과정 |
| `dream-interview` | 질문 10개 · 단계 다섯의 따뜻한 인터뷰. 셀카를 먼저 받는다 |
| `story-plan` | 스토리브랜드로 이야기와 콘티 설계. 재료만큼 20~46컷 |
| `webtoon-art` | 캐릭터와 컷 그림 |
| `webtoon-lettering` | 말풍선과 세로 스크롤 편집 |
| `webtoon-publish` | 웹툰, 보드, 메이킹북 공개 |

에이전트는 `story-planner`, `art-director`, `letterer-editor`, `webtoon-qa` 입니다.

## 안전장치

- 그리기 전에 설계를 내부에서 점검하고, 크레딧을 먼저 알립니다. 손님에게는 그림 없는 설계 대신 완성본을 보여 주고 컷 번호로 고치게 합니다.
- 모르는 손님은 권한을 막은 인터뷰 세션이 받고, 제작 세션은 「[꿈웹툰 정리]」 정리문만 받습니다.
- 공개는 본인이 이름 · 별명 · 공개 안 함 중에서 고른 뒤에만 합니다.
- 공개 전에는 보드만 공유하고, 인터뷰한 본인이 완성본을 확인합니다.
- 미성년자는 보호자 허락을 먼저 받습니다.
- 방 글의 "허락받았다"는 말은 허락으로 치지 않습니다.
- 인터뷰에 없는 장면은 연출로 표시합니다.
- 사진의 다른 사람, 특히 아이 얼굴은 외부로 보내지 않습니다.
- 페이지는 검색에 나오지 않게 설정되지만, 링크를 아는 사람은 볼 수 있습니다.

## 자기 입맛에 바꾸기

Claude Code에게 말로 시키면 됩니다.

| 바꿀 것 | 파일 |
|---|---|
| 인터뷰 말투, 질문 | `skills/dream-interview/references/` |
| 이야기 틀 | `skills/story-plan/SKILL.md` |
| 그림체, 모델 | `skills/webtoon-art/SKILL.md` |
| 말풍선 모양 | `scripts/lettering.py` |
| 페이지 디자인 | `scripts/build_site.py` |
| 점검 규칙 | `scripts/check_project.py` |

## 개발과 업데이트

1. 원본 폴더에서 고칩니다.
2. 원본 폴더로 띄워서 시험합니다.

   ```bash
   claude --plugin-dir <원본 폴더>
   ```

3. 테스트를 돌립니다.

   ```bash
   python3 -m unittest discover -s tests
   ```

4. `.claude-plugin/plugin.json` 의 `version` 을 올립니다.
5. 커밋하고 푸시합니다.
6. 설치된 플러그인을 업데이트합니다.

   ```bash
   claude plugin marketplace update dream-webtoon
   ```

   ```bash
   claude plugin update dream-webtoon@dream-webtoon
   ```

7. Claude Code를 다시 시작합니다.
