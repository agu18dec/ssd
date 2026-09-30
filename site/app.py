"""Speculative Self-Distillation: the blog. `python site/app.py` serves on :5001; export/build_static.py freezes it."""
from pathlib import Path

from fasthtml.common import *

import figures as F
from method_anim import MethodFigure

HERE = Path(__file__).resolve().parent
PAPER = "https://openreview.net/pdf?id=HczpgMR6S3"
CODE = "https://anonymous.4open.science/r/Speculative-Self-Distillation/"
AUTHORS = [("Shayan Talaei", "*", 1), ("Agam Bhatia", "*", 1), ("Arshia Soltani Moakhar", "", 1),
           ("Jonas Hübotter", "", 2), ("Amin Saberi", "", 1), ("Azalia Mirhoseini", "", 1)]
AFFIL = {1: "Stanford University", 2: "ETH Zürich"}
BIBTEX = r"""@misc{talaei2026ssd,
  title  = {Speculative Self-Distillation enables Efficient Knowledge Internalization},
  author = {Talaei, Shayan and Bhatia, Agam and Soltani Moakhar, Arshia and
            H{\"u}botter, Jonas and Saberi, Amin and Mirhoseini, Azalia},
  year   = {2026}
}"""

hdrs = (
    Meta(name="viewport", content="width=device-width, initial-scale=1"),
    Link(rel="preconnect", href="https://fonts.googleapis.com"),
    Link(rel="stylesheet", href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400"
         "&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap"),
    Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css"),
    Script(src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js", defer=True),
    Script(src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js", defer=True),
    Link(rel="stylesheet", href="static/site.css"),
    Script(src="static/anim.js", defer=True),
    Socials(title="Speculative Self-Distillation", site_name="SSD", description="Let the student write. Let the teacher step in only where it matters.",
            image="static/og.png", url=""),
)
app, rt = fast_app(pico=False, hdrs=hdrs, static_path=str(HERE), live=False, default_hdrs=False)


def Sn(*c): return Span(*c, cls="sn")          # sidenote: margin on wide screens, inline aside on narrow ones
def Sec(sid: str, num: str, title: str, *c): return Section(Div(Span(num, cls="num"), H2(title), cls="sec-h"), *c, id=sid)
def Cap(*c): return P(*c, cls="cap")
def Stat(big: str, small: str): return Div(Div(big, cls="stat-b"), Div(small, cls="stat-s"), cls="stat")


def hero():
    names = []
    for i, (n, star, a) in enumerate(AUTHORS):
        names.append(Span(n, Sup(f"{a}{star}"), cls="au"))
    return Header(
        Div("research blog  ·  self-distillation  ·  2026", cls="kicker"),
        H1("Speculative", Br(), "Self‑Distillation"),
        P("Let the student write. Let the teacher step in only where it matters.", cls="dek"),
        Div(*names, cls="authors"),
        Div(*[Span(Sup(k), v, cls="af") for k, v in AFFIL.items()], Span(Sup("*"), "equal contribution", cls="af"), cls="affils"),
        Div(A("Paper", href=PAPER, cls="pill"), A("Code", href=CODE, cls="pill"), A("BibTeX", href="#cite", cls="pill ghost"),
            cls="pills"),
        cls="hero")


def tldr():
    return Div(
        P(Strong("TL;DR. "), "To bake a document into a model's weights, you can let the same model read the document and act as a teacher for "
          "its own closed-book self. Should the teacher or the student write the training rollouts? ", Em("Neither, mostly. "),
          "SSD lets the student write and hands the pen to the teacher only on the few tokens where the document changes the answer. "
          "It matches on-policy accuracy with far fewer supervised tokens and forgets less along the way.", cls="tldr-p"),
        Div(Stat("45%", "fewer supervised tokens than on-policy, on average over 3 tasks"),
            Stat("3×", "less forgetting than on-policy SDFT  (Δ −1.4 vs −4.5)"),
            Stat("16%", "teacher tokens at inference reach 74% accuracy (teacher alone: 80%)"), cls="stats"),
        cls="tldr")


def body():
    return (
        Figure(MethodFigure(),
               Cap(Strong("The SSD decoding loop. "), "Student and teacher are the same model; only the teacher sees the document. At every position both "
                   "propose a next-token distribution, and if they diverge by more than τ the teacher picks the token. Switch tabs to see how τ "
                   "slides between off-policy (τ → 0) and on-policy (τ → ∞). Rollouts follow the paper's running example; the per-step "
                   "distributions and δ values are illustrative."), cls="wide"),

        Sec("idea", "01", "Knowledge in the weights, not the prompt",
            P("Models keep needing facts they never saw in pretraining: an internal memo, last week's news, a niche corner of chemistry. "
              "Stuffing them into the prompt works, but it costs context on every query and the model can still miss what's in front of it. "
              "The alternative is to ", Em("internalize"), " the knowledge: train it into the weights once."),
            P("Self-distillation does this with no extra model. Give the document ", I("C"), " to the model and it becomes a teacher "
              "$\\pi_T(\\cdot\\mid x, C)$. The same model without the document is the student $\\pi_\\theta(\\cdot\\mid x)$. Train the student to match the "
              "teacher token by token:",
              Sn("Methods differ only in the rollout policy $\\pi_{\\text{gen}}$; the per-token loss $D$ is a KL/JSD divergence in all of them.")),
            Div("$$\\mathcal{L}(\\theta)=\\mathbb{E}_{y\\sim\\color{#b4531b}{\\pi_{\\text{gen}}}}\\Big[\\tfrac{1}{|y|}\\sum_t D\\big(\\pi_T(\\cdot\\mid x,C,y_{<t})\\,\\|\\,\\pi_\\theta(\\cdot\\mid x,y_{<t})\\big)\\Big]$$",
                cls="eq"),
            P("The whole question is ", Strong("who writes the rollout $y$"), ". If the teacher writes it, that's ", Span("off-policy", cls="k-off"),
              ". If the student writes it, that's ", Span("on-policy", cls="k-on"), ".")),

        Sec("why", "02", "Off-policy learns fast, on-policy learns right",
            P("Off-policy reaches its plateau about 5× faster, but the plateau is lower: it trains the student on the teacher's states, "
              "which the student won't visit at test time. On-policy fixes that mismatch but crawls. Why so slow? Look at the ",
              Em("signal"), ", the per-token loss, which is exactly how much the teacher has left to say."),
            Figure(F.signal(), Cap(Strong("Right panel: the key diagnostic. "), "Along an on-policy rollout, the teacher–student gap collapses after a "
                                   "handful of tokens. Once the student has wandered off, the teacher, conditioned on the student's prefix, just "
                                   "politely continues it. Wikipedia task, Qwen3-4B-Instruct."), cls="wide"),
            P("Most on-policy tokens carry almost no signal, and the few that do come right at the start. That's where the compute goes to waste.")),

        Sec("inflection", "03", "Inflection tokens",
            P("Asked about the marketing team, student and teacher agree on “Marketing team is …”. Then they split: the teacher, "
              "who read the memo, wants “led by Lina Okafor”; the student drifts into “mainly focused on creating the …”. "
              "We call such a position an ", Strong("inflection token"), ": $\\delta_t = D_{\\text{switch}}(\\pi_\\theta \\,\\|\\, \\pi_T) > \\tau$."),
            Figure(F.fork(), Cap("What happens after an inflection position. On-policy keeps the student's continuation, and every token after it "
                                 "is a ", Em("transient state"), ": the update is about to teach the student ", Em("not"),
                                 " to go there, so supervising those states is spent on a path that will disappear."), cls="wide"),
            P("An on-policy run has to rediscover each such fork one gradient step at a time. Off-policy sees all of them at once, but on the teacher's text.",
              Sn("This is the “transient state” argument of §3.1 in the paper: states produced by a policy the update is explicitly changing."))),

        Sec("method", "04", "SSD: one rule, one knob",
            P("So let the student write, and swap in the teacher exactly at inflection tokens. It's speculative decoding turned into a "
              "training signal: the student drafts, and the teacher overrides only when it strongly disagrees."),
            Pre(Code(Span("for", cls="kw"), " t = 1, 2, … until EOS:\n"
                     "    p_S, p_T = student(x, y<t), teacher(x, C, y<t)\n",
                     Span("    if D_switch(p_S ‖ p_T) > τ:", cls="hl"), "   ", Span("# inflection token", cls="cm"), "\n"
                     "        y_t ~ p_T                  ", Span("# teacher writes", cls="cm t"), "\n"
                     "    else:\n"
                     "        y_t ~ p_S                  ", Span("# student writes", cls="cm s"), "\n"
                     "    loss += D(p_T ‖ p_S)           ", Span("# supervise every position", cls="cm"), "\n"), cls="algo"),
            P("One threshold spans the whole family: ", Strong("τ → 0"), " recovers off-policy, ", Strong("τ → ∞"), " recovers on-policy.",
              Sn("With JSD as $D_{\\text{switch}}$ the divergence is bounded by $\\ln 2\\approx 0.69$, so any τ above that is exactly on-policy."),
              " Rollouts stay close to what the student will actually do, but carry the teacher's signal at the moments that matter.")),

        Sec("results", "05", "On-policy accuracy at off-policy speed",
            P("Three closed-book QA tasks, all with Qwen3-4B-Instruct as both student and teacher: a synthetic ", Strong("company memo"),
              " (private knowledge), a post-cutoff ", Strong("Wikipedia"), " article (knowledge update), and SciKnowEval ",
              Strong("chemistry"), " (skill acquisition). The x-axis is supervised tokens, a FLOPs-proportional budget."),
            Figure(F.headline(), Cap("Drag the budget slider. SSD climbs with off-policy's early slope, then keeps going to on-policy's plateau, "
                                     "and finishes with ", Strong("44%, 34% and 57%"), " fewer supervised tokens. Faint dots are raw evaluations; lines are smoothed."),
                   cls="wide")),

        Sec("knob", "06", "Turning the knob",
            Div(Div(P("Sweeping τ traces a Pareto frontier from the off-policy corner to the on-policy corner. Small τ is cheap but "
                      "caps accuracy; large τ is accurate but slow. In between, SSD gets both."),
                    P("Hover the points. Anything in τ ∈ [0.2, 0.5] gives most of on-policy's accuracy for little more than off-policy's cost."),
                    cls="side-t"),
                Figure(F.tau_frontier(), Cap("Company Memo, JSD switch, 8 epochs."), cls="side-f"), cls="side")),

        Sec("curriculum", "07", "A curriculum for free",
            P("Nobody tells SSD when to stop asking the teacher. Early on, student and teacher disagree often, and up to 40% of tokens come from "
              "the teacher. As the student absorbs the document, the switch fires less and less, and every τ drifts toward on-policy."),
            Figure(F.curriculum(), Cap("Teacher share decays with no external schedule, and response length settles as the student stops "
                                       "rambling before the switch catches it. Company Memo."), cls="wide")),

        Sec("forgetting", "08", "…and it forgets less",
            P("Learning new facts usually costs old skills. Following the SDFT protocol (Qwen2.5-7B on SciKnowEval chemistry), we score "
              "in-domain accuracy against the average change on six general benchmarks: HellaSwag, HumanEval, IFEval, MMLU, TruthfulQA and Winogrande."),
            Div(Figure(F.forgetting(), Cap("Error bars: 95% CI over samples."), cls="side-f"),
                Div(P("Off-policy methods learn the skill and drop about 6.6 points elsewhere. On-policy SDFT forgets less (−4.5). SSD lands in the "
                      "corner nobody else reaches: the ", Strong("best SciQA (71.6)"), ", the ", Strong("least forgetting (−1.4)"),
                      ", and ", Strong("22% fewer tokens"), " than SDFT."), cls="side-t"), cls="side rev")),

        Sec("routing", "09", "Bonus: the switch works at inference, too",
            P("Forget training for a moment. Just decode with the switch, where the teacher sees the answer and the student doesn't, and count how "
              "few teacher tokens it takes to steer the rollout. On SciKnowEval chemistry, routing ", Strong("15.7%"), " of tokens to the teacher "
              "gets within 6 points of the pure teacher."),
            Figure(F.routing(), Cap("JSD-routed decoding, no weight updates. 507 chemistry questions, Qwen3-4B-Instruct."), cls="narrow"),
            P("This is the intuition behind SSD in its rawest form: the teacher's knowledge is concentrated in a handful of decisive tokens.")),

        Sec("next", "10", "Limits & what's next",
            Ul(Li(Strong("Short answers. "), "Our tasks are closed-book QA. Long reasoning traces, where on-policy self-distillation is known to struggle, "
                  "are the natural next test: anchor only the critical steps, and let the student carry the rest."),
               Li(Strong("One axis at a time. "), "We froze the teacher and the question distribution. EMA teachers and uncertainty-targeted "
                  "questions are orthogonal and should compose."),
               Li(Strong("Beyond Qwen3-4B. "), "Scale, other model families, and other switch rules are open."))),

        Section(Div(Span("", cls="num"), H2("Cite"), cls="sec-h"),
                Div(Button("copy", cls="copy", type="button"), Pre(Code(BIBTEX), cls="bib"), cls="bibwrap"), id="cite"),
    )


def nav():
    items = [("idea", "Idea"), ("why", "Why"), ("inflection", "Inflection"), ("method", "Method"), ("results", "Results"),
             ("knob", "τ"), ("forgetting", "Forgetting"), ("cite", "Cite")]
    return Nav(A("SSD", href="#top", cls="brand"), Div(*[A(t, href=f"#{i}", data_sec=i) for i, t in items], cls="nav-l"),
               Div(cls="progress"), cls="topnav")


CAPTURE = {"method": MethodFigure, "fork": F.fork, "signal": F.signal, "headline": F.headline,
           "tau_frontier": F.tau_frontier, "curriculum": F.curriculum, "forgetting": F.forgetting, "routing": F.routing}


@rt
def index(capture: str = ""):
    if capture in CAPTURE:
        return Title(f"SSD · {capture}"), Main(CAPTURE[capture](), cls=f"capture-main cap-{capture}", data_capture=capture)
    return (Title("Speculative Self-Distillation"),
            nav(), Main(hero(), tldr(), *body(), cls="page", id="top"),
            Footer(P("Speculative Self-Distillation · Stanford University & ETH Zürich · 2026"), cls="foot"))


serve(port=5001, reload=False)
