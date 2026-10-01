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
LOGOS = {1: ("static/logos/stanford.svg", "Stanford University"), 2: ("static/logos/eth.svg", "ETH Zürich")}
DESC = "SSD lets the student write its own training rollouts and hands the pen to the teacher only on the few tokens where the document changes the answer."
MEDIA = [("method loop", "method_ssd"), ("on-policy loop", "method_onpolicy"), ("inflection fork", "fork"), ("signal", "signal"),
         ("headline", "headline"), ("τ frontier", "tau_frontier"), ("curriculum", "curriculum")]
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
    Socials(title="Speculative Self-Distillation", site_name="SSD", description=DESC, image="static/media/method_ssd.gif", url=""),
)
app, rt = fast_app(pico=False, hdrs=hdrs, static_path=str(HERE), live=False, default_hdrs=False)


def Sn(*c): return Span(*c, cls="sn")          # sidenote: margin on wide screens, inline aside on narrow ones
def Sec(sid: str, num: str, title: str, *c): return Section(Div(Span(num, cls="num"), H2(title), cls="sec-h"), *c, id=sid)
def Cap(*c): return P(*c, cls="cap")

# small inline icons for the link pills (stroke icons, 16px)
ICONS = {
    "paper": "M6 2h7l5 5v13a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2zm7 0v5h5M8 13h8M8 17h6",
    "code": "M8 7l-5 5 5 5M16 7l5 5-5 5M13.5 4l-3 16",
    "cite": "M6 3h12v18l-6-4-6 4z",
}


def Pill(label: str, href: str, kind: str):
    icon = NotStr(f'<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" '
                  f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="{ICONS[kind]}"/></svg>')
    return A(icon, label, href=href, cls=f"pill {kind}")


def hero():
    names = [Span(n, Sup(f"{a}{star}"), cls="au") for n, star, a in AUTHORS]
    logos = [Span(Sup(str(k)), Img(src=src, alt=alt, cls=f"logo logo-{k}"), cls="af") for k, (src, alt) in LOGOS.items()]
    return Header(
        H1("Speculative", Br(), "Self‑Distillation"),
        Div(*names, cls="authors"),
        Div(*logos, Span(Sup("*"), "equal contribution", cls="af eq-c"), cls="affils"),
        Div(Pill("Paper", PAPER, "paper"), Pill("Code", CODE, "code"), Pill("BibTeX", "#cite", "cite"), cls="pills"),
        cls="hero")


def intro():
    return Div(
        P("Deployed language models keep running into knowledge they were never trained on: a company's internal documents, "
          "facts that changed after the training cutoff, the terminology of a specialised field. Putting that material in the prompt "
          "works, but every query pays to process it again, context is limited, and models do not always use what is in it. For "
          "knowledge that will be needed over and over, it makes more sense to train it into the weights."),
        P("Self-distillation does this without labels or a larger model. The model reads the document and acts as a teacher for "
          "itself without the document. This post is about one design choice in that recipe, who generates the training rollouts, "
          "and how it decides what self-distillation costs. Our method, ", Strong("Speculative Self-Distillation (SSD)"),
          ", lets the student generate and hands over to the teacher only at tokens where the document changes the prediction. "
          "On three knowledge-acquisition tasks it matches on-policy self-distillation with 45% fewer supervised tokens on average, "
          "and it forgets less of the model's general ability."),
        cls="intro-text")


def body():
    return (
        Figure(MethodFigure(),
               Cap(Strong("The SSD decoding loop. "), "Student and teacher are the same model; only the teacher sees the document. "
                   "At each position both propose a next-token distribution, and if they differ by more than a threshold τ the teacher "
                   "picks the token. The tabs show how τ → 0 and τ → ∞ recover off-policy and on-policy distillation. The rollout is "
                   "the paper's running example; the per-step distributions and δ values are illustrative."), cls="wide"),

        Sec("idea", "01", "Self-distillation and its cost",
            P("In self-distillation the model given the document ", I("C"), " is the teacher, $\\pi_T(\\cdot\\mid x, C)$, and the same "
              "model without it is the student, $\\pi_\\theta(\\cdot\\mid x)$. The student is trained to match the teacher token by token:",
              Sn("The teacher is kept frozen at the initial weights, so all methods are compared against the same target.")),
            Div("$$\\mathcal{L}(\\theta)=\\mathbb{E}_{y\\sim\\color{#b4531b}{\\pi_{\\text{gen}}}}\\Big[\\tfrac{1}{|y|}\\sum_t D\\big(\\pi_T(\\cdot\\mid x,C,y_{<t})\\,\\|\\,\\pi_\\theta(\\cdot\\mid x,y_{<t})\\big)\\Big]$$",
                cls="eq"),
            P("Methods differ only in the rollout policy $\\pi_{\\text{gen}}$. If the teacher writes the rollout, the method is ",
              Span("off-policy", cls="k-off"), "; if the student writes it, it is ", Span("on-policy", cls="k-on"), ". On-policy "
              "self-distillation (SDFT) reaches higher accuracy, because the student is trained on the kind of text it will produce at "
              "test time. It is also slow: in our experiments it needs several times more supervised tokens than "
              "off-policy training to converge. If internalizing a document is to be routine, for example every time a knowledge base "
              "is updated, that cost matters.")),

        Sec("why", "02", "Where on-policy training spends its tokens",
            P("To see why on-policy training is slow, we look at the per-token loss along a rollout. It measures how much teacher and "
              "student disagree at a position, and so how much the student can learn from that token. We call it the ", Strong("signal"), "."),
            Figure(F.signal(), Cap(Strong("Off- vs on-policy self-distillation on the Wikipedia task. "), "Left: off-policy converges "
                                   "about 5× faster but saturates lower. Middle: off-policy starts with a much larger per-token loss. "
                                   "Right: per-token loss by position within a rollout."), cls="wide"),
            P("Teacher-written rollouts carry more signal from the start. Along student-written rollouts the signal is high for the "
              "first tokens and then drops. The student writes without the document and soon reaches states unrelated to it; "
              "conditioned on such a prefix, the teacher's distribution falls back close to the student's and there is little left "
              "to correct. Most on-policy supervised tokens therefore go to positions where the teacher adds little.")),

        Sec("inflection", "03", "Inflection tokens",
            P("Take the prompt “tell me about the marketing team of the company”. Student and teacher agree on “Marketing team is”, "
              "then diverge: the teacher, which has read the memo, continues with “led by Lina Okafor”, while the student continues "
              "with a generic “mainly focused on creating the …”. We call such a position an ", Strong("inflection token"),
              ": a position $t$ where $\\delta_t = D_{\\text{switch}}(\\pi_\\theta \\,\\|\\, \\pi_T) > \\tau$."),
            Figure(F.fork(), Cap("After an inflection position, SSD lets the teacher continue. On-policy keeps the student's token, "
                                 "and the tokens after it are ", Em("transient states"), "."), cls="wide"),
            P("The tokens after an on-policy inflection are transient: the update at the inflection moves the student away from "
              "“mainly”, so it will rarely reach those states again, and supervision spent on them is largely wasted. On-policy "
              "training learns such branch points one at a time over many updates; off-policy training sees all of them at once, but "
              "only on text the student would not write.")),

        Sec("method", "04", "Speculative Self-Distillation",
            P("SSD keeps the rollout on the student where the two models agree and switches to the teacher where they do not. The "
              "student generates by default; at each position we compare the two next-token distributions, and if they differ by "
              "more than τ the teacher generates that token. As in speculative decoding, one model drafts and the other checks, but "
              "here a rejected token is written by the teacher and the result is used for training. Every position is supervised "
              "with the same loss as before."),
            Pre(Code(Span("for", cls="kw"), " t = 1, 2, … until EOS:\n"
                     "    p_S, p_T = student(x, y<t), teacher(x, C, y<t)\n",
                     Span("    if D_switch(p_S ‖ p_T) > τ:", cls="hl"), "   ", Span("# inflection token", cls="cm"), "\n"
                     "        y_t ~ p_T                  ", Span("# teacher writes", cls="cm t"), "\n"
                     "    else:\n"
                     "        y_t ~ p_S                  ", Span("# student writes", cls="cm s"), "\n"
                     "    loss += D_loss(p_T ‖ p_S)      ", Span("# supervise every position", cls="cm"), "\n"), cls="algo"),
            P("τ is the only new hyperparameter. τ → 0 recovers off-policy distillation and τ → ∞ recovers on-policy distillation.",
              Sn("With JSD as $D_{\\text{switch}}$ the divergence is bounded by $\\ln 2\\approx 0.69$, so any larger τ is exactly "
                 "on-policy."))),

        Sec("results", "05", "Results",
            P("We follow the SDFT evaluation protocol with Qwen3-4B-Instruct as both student and teacher, on three closed-book QA "
              "tasks: ", Strong("Company Memo"), " (a synthetic internal document), ", Strong("Wikipedia"), " (an article published "
              "after the model's training cutoff) and ", Strong("Science Q&A"), " (SciKnowEval chemistry). Cost is measured in "
              "supervised tokens, the number of positions the loss is computed on, which is roughly proportional to compute."),
            Figure(F.headline(), Cap("Test accuracy against supervised tokens. The slider compares methods at the same budget. Faint "
                                     "dots are raw evaluations; lines are smoothed."), cls="wide"),
            P("On all three tasks SSD improves almost as fast as off-policy early on and then continues to on-policy accuracy, using ",
              Strong("44%"), ", ", Strong("34%"), " and ", Strong("57%"), " fewer supervised tokens than on-policy. On Science Q&A "
              "it finishes about 3 points above on-policy and 15 above off-policy.")),

        Sec("knob", "06", "Choosing τ",
            Div(Div(P("Sweeping τ traces the trade-off between the two endpoints. Small τ is cheap but limits accuracy, as in "
                      "off-policy training; large τ approaches on-policy accuracy and cost. Intermediate values reach higher accuracy "
                      "than off-policy while converging faster than on-policy. With JSD as the switch, τ between 0.2 and 0.5 works well."),
                    P("The teacher's share also changes during training. Early on the two models disagree often, and at the lowest "
                      "threshold up to 40% of tokens come from the teacher. As the student learns the document the switch fires less, "
                      "so training moves toward on-policy without a schedule (figure below)."), cls="side-t"),
                Figure(F.tau_frontier(), Cap("Final accuracy vs supervised tokens across τ, Company Memo. The curve is a guide to "
                                             "the eye."), cls="side-f"), cls="side"),
            Figure(F.curriculum(), Cap("SSD on Company Memo for several JSD thresholds. Left: fraction of rollout tokens written by "
                                       "the teacher. Right: mean response length."), cls="wide")),

        Sec("forgetting", "07", "Forgetting",
            Div(Figure(F.forgetting(), Cap("In-domain SciQA accuracy against the mean change on six general benchmarks (Qwen2.5-7B). "
                                           "Error bars: 95% CI."), cls="side-f"),
                Div(P("Training on new knowledge can degrade other skills. Following SDFT, we fine-tune Qwen2.5-7B on SciKnowEval "
                      "chemistry and measure the average change on six general benchmarks. (Qwen3-4B showed little forgetting under "
                      "any method.)"),
                    P("Off-policy methods lose about 6.6 points and on-policy SDFT loses 4.5. SSD loses 1.4, with the best SciQA "
                      "accuracy (71.6) and 22% fewer supervised tokens than SDFT."), cls="side-t"),
                cls="side rev")),

        Sec("routing", "08", "Switching at inference time",
            P("The same switch can be used for decoding without any training. The teacher sees the question with its answer, the "
              "student sees only the question, and the JSD between them decides who emits each token."),
            Figure(F.routing(), Cap("JSD-routed decoding on 507 SciKnowEval chemistry questions, Qwen3-4B-Instruct, no weight "
                                    "updates. Right: share of tokens from the teacher."), cls="narrow"),
            P("With 15.7% of tokens from the teacher, accuracy is 74.0%, compared with 80.3% for the teacher alone and 13.8% for the "
              "student. Much of the teacher's advantage comes from a small number of tokens, which is what SSD relies on.")),

        Section(Div(Span("", cls="num"), H2("Cite"), cls="sec-h"),
                Div(Button("copy", cls="copy", type="button"), Pre(Code(BIBTEX), cls="bib"), cls="bibwrap"), id="cite"),
    )


def nav():
    items = [("idea", "Idea"), ("why", "Why"), ("inflection", "Inflection"), ("method", "Method"), ("results", "Results"),
             ("knob", "τ"), ("forgetting", "Forgetting"), ("routing", "Inference"), ("cite", "Cite")]
    return Nav(A("SSD", href="#top", cls="brand"), Div(*[A(t, href=f"#{i}", data_sec=i) for i, t in items], cls="nav-l"),
               Div(cls="progress"), cls="topnav")


CAPTURE = {"method": MethodFigure, "fork": F.fork, "signal": F.signal, "headline": F.headline,
           "tau_frontier": F.tau_frontier, "curriculum": F.curriculum, "forgetting": F.forgetting, "routing": F.routing}


@rt
def index(capture: str = ""):
    if capture in CAPTURE:
        return Title(f"SSD · {capture}"), Main(CAPTURE[capture](), cls=f"capture-main cap-{capture}", data_capture=capture)
    return (Title("Speculative Self-Distillation"), Meta(name="description", content=DESC),
            nav(), Main(hero(), intro(), *body(), cls="page", id="top"),
            Footer(Div(*[Img(src=s, alt=a, cls="logo") for s, a in LOGOS.values()], cls="foot-logos"),
                   P("Speculative Self-Distillation · Stanford University & ETH Zürich · 2026"), cls="foot"))


serve(port=5001, reload=False)
