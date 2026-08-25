# -*- coding: utf-8 -*-
"""
风雅阁 · 诗词一句 （横屏水墨画版）
- 背景 = 桌面同一目录下的「水墨背景.png」（横向文人水墨山水）
- subsample 整数缩放为 889x500 横屏，纯标准库即可完成
- 上部半透明宣纸卡托住正文，下部朱印按钮
- 点击后后台线程在线随机获取真实古诗词名句，绝不卡界
零第三方依赖。背景为本地文件，离线可用。
"""
import os
import json
import queue
import urllib.request
import tkinter as tk
import threading

API_MAIN = "https://v1.jinrishici.com/all.json"                # 古诗词·一言（在线诗词）
API_ESSAY = "https://hub.saintic.com/openservice/sentence/all.json"  # 在线古文库（含诗·词·歌·赋·古籍）
API_BACK = "https://poetry.palemoky.com/api/sentence/random"    # 诗泉备用（已404，保留兜底）

BASE = os.path.dirname(os.path.abspath(__file__))
BG_FILE = os.path.join(BASE, "水墨背景.png")   # 本地横屏水墨画

# ===== 本地经典文章/经史子集名句库（离线可用，稳定抽取）=====
CLASSICS = [
    ["不以物喜，不以己悲。居庙堂之高则忧其民，处江湖之远则忧其君。", "范仲淹《岳阳楼记》"],
    ["先天下之忧而忧，后天下之乐而乐。", "范仲淹《岳阳楼记》"],
    ["朝而往，暮而归，四时之景不同，而乐亦无穷也。", "欧阳修《醉翁亭记》"],
    ["醉翁之意不在酒，在乎山水之间也。", "欧阳修《醉翁亭记》"],
    ["落霞与孤鹜齐飞，秋水共长天一色。", "王勃《滕王阁序》"],
    ["穷且益坚，不坠青云之志。", "王勃《滕王阁序》"],
    ["海内存知己，天涯若比邻。", "王勃《送杜少府之任蜀州》"],
    ["学而时习之，不亦说乎？有朋自远方来，不亦乐乎？", "《论语·学而》"],
    ["三人行，必有我师焉。择其善者而从之，其不善者而改之。", "《论语·述而》"],
    ["温故而知新，可以为师矣。", "《论语·为政》"],
    ["己所不欲，勿施于人。", "《论语·颜渊》"],
    ["敏而好学，不耻下问。", "《论语·公冶长》"],
    ["不义而富且贵，于我如浮云。", "《论语·述而》"],
    ["夫战，勇气也。一鼓作气，再而衰，三而竭。", "《左传·曹刿论战》"],
    ["小大之狱，虽不能察，必以情。", "《左传·曹刿论战》"],
    ["天将降大任于是人也，必先苦其心志，劳其筋骨，饿其体肤。", "《孟子·告子下》"],
    ["生于忧患，而死于安乐也。", "《孟子·告子下》"],
    ["鱼，我所欲也；熊掌，亦我所欲也。二者不可得兼，舍鱼而取熊掌者也。", "《孟子·告子上》"],
    ["得道者多助，失道者寡助。", "《孟子·公孙丑下》"],
    ["先帝创业未半而中道崩殂，今天下三分，益州疲弊，此诚危急存亡之秋也。", "诸葛亮《出师表》"],
    ["亲贤臣，远小人，此先汉所以兴隆也。", "诸葛亮《出师表》"],
    ["山不在高，有仙则名；水不在深，有龙则灵。斯是陋室，惟吾德馨。", "刘禹锡《陋室铭》"],
    ["谈笑有鸿儒，往来无白丁。", "刘禹锡《陋室铭》"],
    ["出淤泥而不染，濯清涟而不妖。", "周敦颐《爱莲说》"],
    ["千里之行，始于足下。", "《老子》"],
    ["知人者智，自知者明。胜人者有力，自胜者强。", "《老子》"],
    ["路漫漫其修远兮，吾将上下而求索。", "屈原《离骚》"],
    ["天行健，君子以自强不息；地势坤，君子以厚德载物。", "《周易》"],
    ["玉不琢，不成器；人不学，不知道。", "《礼记·学记》"],
    ["物有所不足，智有所不明。", "《楚辞·卜居》"],
    ["与善人居，如入芝兰之室，久而不闻其香。", "《孔子家语》"],
    ["捐躯赴国难，视死忽如归。", "曹植《白马篇》"],
    ["老骥伏枥，志在千里；烈士暮年，壮心不已。", "曹操《龟虽寿》"],
    ["不鸣则已，一鸣惊人。", "《史记·滑稽列传》"],
    ["桃李不言，下自成蹊。", "《史记·李将军列传》"],
    ["燕雀安知鸿鹄之志哉！", "《史记·陈涉世家》"],
    ["不积跬步，无以至千里；不积小流，无以成江海。", "荀子《劝学》"],
    ["青，取之于蓝，而青于蓝。", "荀子《劝学》"],
    ["不飞则已，一飞冲天；不鸣则已，一鸣惊人。", "《韩非子·喻老》"],
    ["生当作人杰，死亦为鬼雄。", "李清照《夏日绝句》"],
]

# ===== 在线诗词兜底（仅在线失败时）=====
FALLBACK = [
    ["路漫漫其修远兮，吾将上下而求索。", "屈原《离骚》"],
    ["会当凌绝顶，一览众山小。", "杜甫《望岳》"],
    ["山重水复疑无路，柳暗花明又一村。", "陆游《游山西村》"],
    ["长风破浪会有时，直挂云帆济沧海。", "李白《行路难》"],
]

# 横屏窗口尺寸（对应当前背景图 subsample(4) 的结果）
W, H = 889, 500
SEAL = "#b23a2b"


class App:
    def __init__(self, root):
        self.root = root
        root.title("风雅阁 · 诗词一句")
        root.geometry("%dx%d" % (W, H))
        root.resizable(False, False)

        self.cv = tk.Canvas(root, width=W, height=H, highlightthickness=0)
        self.cv.pack()

        # 1) 本地横屏水墨画作背景（整数缩放）
        self._bg = None
        try:
            from tkinter import PhotoImage
            img = PhotoImage(file=BG_FILE)
            w0, h0 = img.width(), img.height()
            k = max(int(w0 / W + 0.5), int(h0 / H + 0.5))
            if k < 1:
                k = 1
            self._bg = img.subsample(k, k)
            bw, bh = self._bg.width(), self._bg.height()
            # 居中摆放
            self._art_id = self.cv.create_image(
                W // 2, H // 2, image=self._bg, anchor="center")
        except Exception:
            self._art_id = self.cv.create_rectangle(0, 0, W, H, fill="#efe9da", outline="")

        # 2) 上部半透明宣纸卡（浮于画面留白，高度随文字自适应）
        self.CARD_W = 540                     # 卡片内宽（正文换行宽度，防越界）
        self.card = self.cv.create_rectangle(
            W // 2 - 300, 40, W // 2 + 300, 250,
            fill="#f7f2e2", outline="#c9b888", width=2)
        self.border = self.cv.create_rectangle(
            W // 2 - 288, 52, W // 2 + 288, 238, outline="#c9b888", width=1)
        self.auth_id = self.cv.create_text(
            W // 2, 195, text="— 网络实时随机 —", fill="#7d7464", font=("KaiTi", 13))

        # 3) 诗词正文（换行宽度=卡片内宽，长句自动在框内换行）
        self.sen_id = self.cv.create_text(
            W // 2, 120, text="点击掌中朱印，求一句诗词",
            fill="#2f2f2f", font=("KaiTi", 22), width=self.CARD_W, justify="center")
        self._fit_card()

        # 4) 朱印按钮（下部）—— 手动求一句
        self.btn = tk.Button(root, text="求 一 句", command=self.on_click,
                             bg="#f7f2e2", fg=SEAL, font=("KaiTi", 15, "bold"),
                             activebackground="#ece4cf", relief="ridge",
                             bd=3, padx=24, pady=8, cursor="hand2")
        self.cv.create_window(W // 2, H - 132, window=self.btn, width=160, height=46)

        # 5) 自动觅句按钮 —— 每 2.5 秒自动获取，可再点暂停
        self.auto_btn = tk.Button(root, text="▷ 自动觅句", command=self.toggle_auto,
                                  bg="#dde6d8", fg="#3a6b35", font=("Microsoft YaHei", 12, "bold"),
                                  activebackground="#cdd9c6", relief="ridge",
                                  bd=2, padx=18, pady=6, cursor="hand2")
        self.cv.create_window(W // 2, H - 80, window=self.auto_btn, width=150, height=40)

        # 6) 底部提示（来源标示）
        self.tip_id = self.cv.create_text(
            W // 2, H - 45, text="点击「求一句」或在「自动觅句」间切换",
            fill="#FFA421", font=("KaiTi", 13))

        self._q = queue.Queue()
        self._busy = False
        self._auto = False           # 是否处于自动觅句状态
        self._auto_job = None        # 自动定时器句柄
        self._poll()

    # ---- 卡片自适应：让宣纸卡包住正文与出处 ----
    def _fit_card(self):
        try:
            # 正文与出处的联合包围盒
            bx = self.cv.bbox(self.sen_id)
            ay = self.cv.bbox(self.auth_id)
            if not bx or not ay:
                return
            x0 = min(bx[0], ay[0]); y0 = min(bx[1], ay[1])
            x1 = max(bx[2], ay[2]); y1 = max(bx[3], ay[3])
            # 卡片比内容多一圈内边距
            pad = 26
            c0 = x0 - pad; c1 = y0 - pad - 8
            c2 = x1 + pad; c3 = y1 + pad + 8
            # 卡片宽度固定=内宽+边距，居中
            half = self.CARD_W // 2 + pad
            cx0 = W // 2 - half
            cx2 = W // 2 + half
            self.cv.coords(self.card, cx0, c1, cx2, c3)
            self.cv.coords(self.border, cx0 + 12, c1 + 12, cx2 - 12, c3 - 12)
        except Exception:
            pass

    # ---- 取词（手动 / 自动共用的入口，带防重入锁）----
    def _request_quote(self):
        if self._busy:
            return False          # 已有取词在进行，返回 False 表示本次未发起
        self._busy = True
        self.btn.config(state="disabled", text="觅 句 中 …")
        threading.Thread(target=self._work, daemon=True).start()
        return True

    def on_click(self):
        self._request_quote()

    # ---- 自动觅句：每 2.5 秒获取一次，可再点击暂停 ----
    def toggle_auto(self):
        if self._auto:
            # 暂停
            self._auto = False
            if self._auto_job is not None:
                self.root.after_cancel(self._auto_job)
                self._auto_job = None
            self.auto_btn.config(text="▷ 自动觅句", bg="#dde6d8", fg="#3a6b35")
        else:
            # 启动
            self._auto = True
            self.auto_btn.config(text="‖ 觅句中·点击暂停", bg="#f2e3be",
                                 fg="#8a6f3f")
            self._auto_tick()    # 立即觅一句

    def _auto_tick(self):
        if not self._auto:
            return
        self._request_quote()              # 若上一拍未完(busy)则本次自动跳过
        # 恒定每 2 秒一拍；取词是后台异步，完成为止由 _poll 释放锁
        self._auto_job = self.root.after(2000, self._auto_tick)

    def _work(self):
        import random
        # ===== 本地库仅以约 10% 概率偶尔露面（形成“偶尔兜底”的感觉），90% 走在线 =====
        if random.random() < 0.10:
            s, a = self._pick_classic()
            self._q.put(("classic", (a, s)))
            return
        # ===== 90%：在线优先，古文库(SaintIC) → 诗词库(今日诗词) =====
        for url in (API_ESSAY, API_MAIN):
            try:
                d = json.loads(_fetch_bytes(url).decode("utf-8"))
                if "data" in d and isinstance(d["data"], dict):
                    # 在线古文库(SaintIC)：诗·词·歌·赋·古籍
                    dt = d["data"]
                    body = dt.get("sentence") or ""
                    if body.strip():
                        au = dt.get("author") or ""
                        nm = dt.get("name") or "逸句"
                        self._q.put(("essay", (au + "《" + nm + "》", body.strip())))
                        return
                if "content" in d:
                    # 在线诗词库(今日诗词)
                    title = d.get("origin") or "逸句"
                    auth = d.get("author") or ""
                    self._q.put(("ok", (auth + "《" + title + "》", d["content"].strip())))
                    return
            except Exception:
                continue
        # 在线失败才回退到本地典籍（断网兜底）
        s, a = self._pick_classic()
        self._q.put(("classic", (a, s)))

    # 从本地库抽取，尽量避开刚显示过的一条，减少重复感
    def _pick_classic(self):
        import random
        if len(CLASSICS) <= 1:
            return CLASSICS[0]
        n = random.randrange(len(CLASSICS))
        for _ in range(5):                 # 兜底时避免与最近一次相同
            if CLASSICS[n] != getattr(self, "_last_local", None):
                break
            n = (n + 1) % len(CLASSICS)
        self._last_local = CLASSICS[n]
        return CLASSICS[n]

    def _poll(self):
        try:
            while True:
                kind, val = self._q.get_nowait()
                if kind == "ok":
                    self.cv.itemconfig(self.auth_id, text=val[0])
                    self.cv.itemconfig(self.sen_id, text=val[1])
                    self.cv.itemconfig(self.tip_id, text="")
                elif kind == "essay":
                    self.cv.itemconfig(self.auth_id, text=val[0])
                    self.cv.itemconfig(self.sen_id, text=val[1])
                    self.cv.itemconfig(self.tip_id, text="")
                elif kind == "classic":
                    self.cv.itemconfig(self.auth_id, text=val[0])
                    self.cv.itemconfig(self.sen_id, text=val[1])
                    self.cv.itemconfig(self.tip_id, text="")
                # 长句智能换行后，让卡片包住内容
                self._fit_card()
                self.btn.config(state="normal", text="求 一 句")
                self._busy = False
        except queue.Empty:
            pass
        self.root.after(60, self._poll)


def _fetch_bytes(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=4) as r:   # 4s 超时，慢请求快速失败重试
        return r.read()


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
