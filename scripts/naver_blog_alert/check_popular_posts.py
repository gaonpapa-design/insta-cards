"""네이버 블로그의 '인기글' 배지를 감지해서 새 인기글이 생겼을 때만 이메일로 알린다.

목록 페이지(PostList)만 방문하고 개별 게시물 페이지는 절대 열지 않는다.
네이버는 게시물 상세 페이지를 열람할 때만 조회수를 올리므로, 목록만 확인하면
블로그 조회수에 영향을 주지 않는다.
"""

import asyncio
import json
import os
import re
import smtplib
from email.mime.text import MIMEText
from pathlib import Path

from playwright.async_api import async_playwright

BLOG_ID = "hjyu82"
BLOG_LIST_URL = f"https://m.blog.naver.com/PostList.naver?blogId={BLOG_ID}&tab=1"
STATE_PATH = Path(__file__).parent / "state.json"
DEBUG_HTML_PATH = Path("debug_page.html")

MOBILE_USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36"
)


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {"seen_popular_post_ids": []}


def save_state(state: dict) -> None:
    STATE_PATH.write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )


async def fetch_popular_posts() -> list[dict]:
    """현재 '인기글' 배지가 붙어 있는 게시물 목록을 반환한다."""
    posts: list[dict] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(user_agent=MOBILE_USER_AGENT)
        await page.goto(BLOG_LIST_URL, wait_until="networkidle", timeout=30000)

        badge_locator = page.locator("text=인기글")
        count = await badge_locator.count()
        for i in range(count):
            badge = badge_locator.nth(i)
            anchor = badge.locator(
                "xpath=ancestor::a[contains(@href, 'PostView')][1]"
            )
            if await anchor.count() == 0:
                continue
            href = await anchor.get_attribute("href")
            title = (await anchor.inner_text()).strip()
            if not href:
                continue
            match = re.search(r"logNo=(\d+)", href)
            post_id = match.group(1) if match else href
            posts.append({"id": post_id, "title": title, "url": href})

        if not posts:
            # 셀렉터가 실제 페이지 구조와 어긋났을 가능성에 대비해 원본 HTML 저장
            DEBUG_HTML_PATH.write_text(await page.content(), encoding="utf-8")

        await browser.close()

    dedup = {p["id"]: p for p in posts}
    return list(dedup.values())


def send_email(new_posts: list[dict]) -> None:
    sender = os.environ["GMAIL_ADDRESS"]
    password = os.environ["GMAIL_APP_PASSWORD"]
    to_addr = os.environ.get("ALERT_EMAIL_TO", sender)

    lines = [f"- {p['title']}\n  {p['url']}" for p in new_posts]
    body = (
        f"hjyu82 네이버 블로그({BLOG_LIST_URL})에 새로운 인기글이 있습니다:\n\n"
        + "\n\n".join(lines)
    )

    msg = MIMEText(body, _charset="utf-8")
    msg["Subject"] = f"[네이버 블로그 알림] 새 인기글 {len(new_posts)}건"
    msg["From"] = sender
    msg["To"] = to_addr

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, [to_addr], msg.as_string())


def main() -> None:
    state = load_state()
    seen = set(state.get("seen_popular_post_ids", []))

    current_posts = asyncio.run(fetch_popular_posts())
    new_posts = [p for p in current_posts if p["id"] not in seen]

    if new_posts:
        send_email(new_posts)
        print(f"Sent alert for {len(new_posts)} new popular post(s).")
    else:
        print("No new popular posts. No alert sent.")

    state["seen_popular_post_ids"] = [p["id"] for p in current_posts]
    save_state(state)


if __name__ == "__main__":
    main()
