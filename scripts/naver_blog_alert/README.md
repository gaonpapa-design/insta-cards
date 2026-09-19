# Naver Blog Popular Post Alert

`m.blog.naver.com/PostList.naver?blogId=hjyu82&tab=1` 목록 페이지에서 '인기글'
배지가 붙은 게시물을 확인하고, 이전에 알리지 않은 새 인기글이 있을 때만
이메일을 보낸다. 개별 게시물 페이지는 열지 않으므로 블로그 조회수에는
영향을 주지 않는다.

## 필요한 GitHub 저장소 시크릿

`Settings > Secrets and variables > Actions > New repository secret` 에서 추가:

| 이름 | 값 |
| --- | --- |
| `GMAIL_ADDRESS` | 발신용 Gmail 주소 (예: gaonpapa@gmail.com) |
| `GMAIL_APP_PASSWORD` | 해당 계정의 Gmail 앱 비밀번호 (2단계 인증 필요, https://myaccount.google.com/apppasswords 에서 발급) |
| `ALERT_EMAIL_TO` | 알림을 받을 이메일 주소 (미설정 시 `GMAIL_ADDRESS`로 발송) |

## 동작 방식

- 매일 00:00 KST(UTC 15:00)에 GitHub Actions가 실행된다.
- `state.json`에 이전에 확인한 인기글 ID 목록을 저장해두고, 이번 실행에서
  발견한 인기글과 비교한다.
- 새 인기글이 있으면 이메일 발송 + `state.json` 갱신 후 커밋.
- 새 인기글이 없으면 이메일을 보내지 않고 `state.json`만 최신 상태로 갱신한다.
- 배지 셀렉터가 아무 것도 못 찾으면 디버깅용으로 `debug_page.html`을
  Actions 아티팩트로 업로드한다. 첫 실행(Run workflow) 후 실제로 인기글이
  있는데도 감지되지 않는다면 이 파일을 보고 셀렉터를 조정해야 한다.

## 수동 실행

저장소의 Actions 탭에서 "Naver Blog Popular Post Alert" 워크플로우를 열고
"Run workflow"로 즉시 테스트할 수 있다.
