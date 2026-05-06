import json
import os
import time
import requests
from playwright.sync_api import sync_playwright

# ─── 환경변수 ───────────────────────────────────────────────
NAVER_ID   = os.environ["NAVER_ID"]
NAVER_PW   = os.environ["NAVER_PW"]
BAND_URL   = os.environ["BAND_URL"]       # ex) https://band.us/band/12345678
GIST_ID    = os.environ["GIST_ID"]        # GitHub Gist ID (replied 저장용)
GH_TOKEN   = os.environ["GH_TOKEN"]       # GitHub Personal Access Token

GIST_FILE  = "replied.json"
KEYWORDS   = json.load(open("keywords.json"))["keywords"]

# ─── Gist로 replied 목록 불러오기 / 저장하기 ─────────────────
def load_replied() -> set:
    headers = {"Authorization": f"token {GH_TOKEN}"}
    res = requests.get(f"https://api.github.com/gists/{GIST_ID}", headers=headers)
    if res.status_code == 200:
        content = res.json()["files"].get(GIST_FILE, {}).get("content", "[]")
        return set(json.loads(content))
    return set()

def save_replied(replied: set):
    headers = {"Authorization": f"token {GH_TOKEN}"}
    payload = {
        "files": {
            GIST_FILE: {"content": json.dumps(list(replied))}
        }
    }
    requests.patch(f"https://api.github.com/gists/{GIST_ID}", headers=headers, json=payload)
    print(f"💾 Gist 저장 완료 ({len(replied)}개)")

# ─── 메인 봇 ─────────────────────────────────────────────────
def run():
    replied = load_replied()
    new_replies = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = ctx.new_page()

        # ── 네이버 로그인 ──
        print("🔐 네이버 로그인 중...")
        page.goto("https://nid.naver.com/nidlogin.login", wait_until="domcontentloaded")
        # JS로 값 입력 (봇 감지 우회)
        page.evaluate(f"document.querySelector('#id').value = '{NAVER_ID}'")
        page.evaluate(f"document.querySelector('#pw').value = '{NAVER_PW}'")
        page.click(".btn_login")
        page.wait_for_timeout(3000)

        # ── 밴드 접속 ──
        print(f"📡 밴드 접속 중: {BAND_URL}")
        page.goto(BAND_URL, wait_until="networkidle")
        page.wait_for_timeout(3000)

        # 스크롤로 게시글 로딩
        for _ in range(3):
            page.keyboard.press("End")
            page.wait_for_timeout(1000)

        # ── 게시글 수집 ──
        posts = page.query_selector_all("div[class*='postWrap'], article[class*='post']")
        print(f"📄 게시글 {len(posts)}개 발견")

        for post in posts:
            try:
                # post ID 추출 (data 속성 or 링크 href)
                post_id = post.get_attribute("data-post-id") or \
                          post.get_attribute("data-logparam") or \
                          post.inner_text()[:30]  # fallback: 앞 30자

                if post_id in replied:
                    continue

                text = post.inner_text()

                for kw in KEYWORDS:
                    if kw["word"] in text:
                        print(f"🎯 키워드 '{kw['word']}' 감지 → 답변 시도")

                        # 댓글창 열기
                        comment_btn = post.query_selector("button[class*='comment'], a[class*='comment']")
                        if comment_btn:
                            comment_btn.click()
                            page.wait_for_timeout(1500)

                        # 댓글 입력창 찾기
                        input_box = post.query_selector(
                            "textarea[class*='comment'], div[contenteditable='true'][class*='comment']"
                        )
                        if input_box:
                            input_box.click()
                            input_box.fill(kw["reply"])
                            page.wait_for_timeout(500)

                            # 전송 버튼 클릭
                            submit_btn = post.query_selector(
                                "button[class*='submit'], button[class*='send'], button[type='submit']"
                            )
                            if submit_btn:
                                submit_btn.click()
                            else:
                                input_box.press("Enter")

                            new_replies.add(post_id)
                            print(f"  ✅ 답변 완료: {post_id[:20]}...")
                            time.sleep(2)
                        else:
                            print(f"  ⚠️ 입력창 없음 (선택자 확인 필요)")
                        break

            except Exception as e:
                print(f"  ❌ 오류: {e}")
                continue

        browser.close()

    # 새로 답변한 것만 추가해서 저장
    if new_replies:
        replied.update(new_replies)
        save_replied(replied)
        print(f"\n🎉 이번 실행 답변: {len(new_replies)}개")
    else:
        print("\n💤 새로운 키워드 게시글 없음")

if __name__ == "__main__":
    run()
