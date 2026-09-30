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
def Stat(big: str, small: str): return Div(Div(big, cls="stat-b"), Div(small, cls="stat-s"), cls="stat")

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


def tldr():
    return Div(
        P(Strong("TL;DR. "), "One way to train a document into a language model's weights is self-distillation: the model reads the document and "
          "acts as a teacher for the same model without the document. Methods differ in who writes the training rollouts. If the teacher writes them, learning is fast but the student is trained on text it would never produce. "
          "If the student writes them, it learns on its own distribution, but most of the rollout carries almost no signal. ",
          Strong("Speculative Self-Distillation (SSD)"), " lets the student write and switches to the teacher only on the few "
          "tokens where the document changes what should come next. It reaches on-policy accuracy with far fewer supervised tokens "
          "and forgets less of the model's general capabilities.", cls="tldr-p"),
        Div(Stat("45%", "fewer supervised tokens than on-policy self-distillation, averaged over three tasks"),
            Stat("3×", "less forgetting of general skills than on-policy SDFT (Δ −1.4 vs −4.5 points)"),
            Stat("16%", "teacher tokens at inference reach 74% accuracy, vs 80% for the teacher alone"), cls="stats"),
        cls="tldr")


def body():
    return (
        Figure(MethodFigure(),
               Cap(Strong("The SSD decoding loop. "), "The student and the teacher are the same model; only the teacher sees the "
                   "document. At every position, both propose a distribution over the next token. When the two disagree by more than a "
                   "threshold τ, the teacher picks the token; otherwise the student does. Switch tabs to see how the same knob recovers "
                   "off-policy distillation (τ → 0) and on-policy distillation (τ → ∞). The rollout follows the paper's running example; "
                   "the per-step distributions and δ values are illustrative."), cls="wide"),

        Sec("idea", "01", "Knowledge in the weights",
            P("Language models are often asked about things they never saw during pretraining: a company's internal memo, an event "
              "from last month, a specialised corner of chemistry. The usual answer is to put the relevant text in the prompt and let "
              "in-context learning do the rest. This works, but the document takes up context on every query, each query pays to process it "
              "again, retrieval has to find the right passage, and models do not always use evidence that is in the context."),
            P("The alternative is to ", Em("internalize"), " the knowledge: train it into the weights once, so the model can use it without "
              "the document at inference time. ", Strong("Self-distillation"), " is one way to do this. Given the document ", I("C"),
              ", the model acts as a teacher, $\\pi_T(\\cdot\\mid x, C)$. The same model without the document "
              "is the student, $\\pi_\\theta(\\cdot\\mid x)$. This needs no larger model and no labels; the training signal comes from the "
              "model's own in-context learning. We train the student to match the teacher token by token,",
              Sn("Throughout, the teacher is frozen at the initial weights so that every method is compared against the same target.")),
            Div("$$\\mathcal{L}(\\theta)=\\mathbb{E}_{y\\sim\\color{#b4531b}{\\pi_{\\text{gen}}}}\\Big[\\tfrac{1}{|y|}\\sum_t D\\big(\\pi_T(\\cdot\\mid x,C,y_{<t})\\,\\|\\,\\pi_\\theta(\\cdot\\mid x,y_{<t})\\big)\\Big]$$",
                cls="eq"),
            P("where ", I("D"), " is a divergence between the two next-token distributions, such as forward KL or Jensen–Shannon. The "
              "methods we compare all use this loss and differ only in the rollout policy $\\pi_{\\text{gen}}$ (highlighted), that is, ",
              Strong("who writes the rollout $y$"), " on which the loss is computed."),
            P("If the teacher writes it, we get ", Span("off-policy", cls="k-off"), " self-distillation: the student imitates the teacher "
              "along the teacher's own text. If the student writes it, we get ", Span("on-policy", cls="k-on"),
              " self-distillation: the student generates freely and the teacher grades every token of what it produced.")),

        Sec("why", "02", "Off-policy vs on-policy",
            P("Off-policy training improves about five times faster than on-policy training but levels off at a lower accuracy. "
              "On-policy training is slower and reaches a higher final accuracy. The standard "
              "explanation for the plateau is train–test mismatch: an off-policy student only ever practises on the teacher's states, "
              "while at test time it has to continue from its own, possibly imperfect, prefixes."),
            P("We look at a different question: why is off-policy training so much more efficient? To study it we use the per-token "
              "loss, which measures how much the teacher and the student disagree at a position and therefore how large the update from "
              "that token is. We call this the ", Strong("signal"), "."),
            Figure(F.signal(), Cap(Strong("Off- vs on-policy self-distillation on the Wikipedia task. "), "Left: off-policy converges about 5× "
                                   "faster but saturates lower. Middle: off-policy starts with a much larger per-token loss and reduces "
                                   "it quickly. Right: the per-token loss as a function of position within a rollout. Along on-policy "
                                   "rollouts, the signal collapses after the first dozen or so tokens."), cls="wide"),
            P("Teacher-written rollouts carry more signal per token from the first training step. Along on-policy rollouts, the signal "
              "is concentrated in the first tokens and then drops. Because the student generates without the document, it soon reaches "
              "states unrelated to the document. Conditioned on such a prefix, the teacher's distribution falls back to one close to the "
              "student's, so there is little to correct and the per-token loss is small."),
            P("As a result, most of the supervised tokens in on-policy training go to positions where the teacher adds little.")),

        Sec("inflection", "03", "Inflection tokens",
            P("Consider the prompt “tell me about the marketing team of the company”. The student and the teacher agree on the opening "
              "words, “Marketing team is …”, and diverge at the next token. The teacher, which has read the memo, continues with “led by "
              "Lina Okafor”. The student continues with a generic “mainly focused on creating the …”."),
            P("We call a position like this an ", Strong("inflection token"), ": a point where having the document substantially changes "
              "the next-token distribution. Formally, position ", I("t"), " is a τ-inflection position if $\\delta_t = D_{\\text{switch}}"
              "(\\pi_\\theta \\,\\|\\, \\pi_T) > \\tau$, for some divergence $D_{\\text{switch}}$ between the student's and the teacher's "
              "next-token distributions."),
            Figure(F.fork(), Cap("What happens after an inflection position. SSD lets the teacher take over and the rollout stays on the "
                                 "informative path. On-policy keeps the student's choice, and every token after it is a ",
                                 Em("transient state"), "."), cls="wide"),
            P("The states after an on-policy inflection are transient. The loss at the inflection token moves the student away from "
              "“mainly”, so after the update it will rarely produce that prefix again, and supervision on the tokens that follow is spent "
              "on a path the student will stop taking.",
              Sn("This is the “transient state” argument of §3.1 in the paper: states produced by a policy that the update is "
                 "explicitly changing.")),
            P("On-policy training therefore learns these branch points one at a time over many updates. Off-policy training covers all "
              "of them in a single rollout (the teacher writes the team lead, the team size and so on), but only on text the teacher "
              "wrote.")),

        Sec("method", "04", "Speculative Self-Distillation",
            P("We want rollouts that stay on the student's distribution where it already agrees with the teacher and switch to the "
              "teacher where the student is about to diverge from it. SSD does this with a single rule. The student generates by default. At every position we compare "
              "the two next-token distributions, and if they diverge by more than τ, the teacher generates that token instead."),
            P("The name comes from speculative decoding, where a cheap draft model proposes tokens and a stronger model verifies them. "
              "Here the student drafts and the teacher checks each token; where it rejects the student's distribution, it writes the "
              "token itself. Every position is still supervised with the same loss as before; only the rollout changes."),
            Pre(Code(Span("for", cls="kw"), " t = 1, 2, … until EOS:\n"
                     "    p_S, p_T = student(x, y<t), teacher(x, C, y<t)\n",
                     Span("    if D_switch(p_S ‖ p_T) > τ:", cls="hl"), "   ", Span("# inflection token", cls="cm"), "\n"
                     "        y_t ~ p_T                  ", Span("# teacher writes", cls="cm t"), "\n"
                     "    else:\n"
                     "        y_t ~ p_S                  ", Span("# student writes", cls="cm s"), "\n"
                     "    loss += D_loss(p_T ‖ p_S)      ", Span("# supervise every position", cls="cm"), "\n"), cls="algo"),
            P("There are two divergences: $D_{\\text{switch}}$ decides who writes the next token, and $D_{\\text{loss}}$ trains the "
              "student. The threshold τ is the only new hyperparameter. As τ → 0 the teacher writes everything and we recover off-policy distillation. As τ → ∞ the teacher never "
              "intervenes and we recover on-policy distillation.",
              Sn("With JSD as $D_{\\text{switch}}$ the divergence is bounded by $\\ln 2\\approx 0.69$, so any τ above that is exactly "
                 "on-policy.")),
            P("Intermediate values keep rollouts close to what the student generates at test time while using the teacher at "
              "inflection tokens.")),

        Sec("results", "05", "Results",
            P("We follow the evaluation protocol of SDFT and test on three closed-book QA tasks, covering private documents, knowledge "
              "updates and domain skills. ", Strong("Company Memo"), " is a synthetic internal document about a fictional cooperative, a "
              "stand-in for private organisational knowledge. ", Strong("Wikipedia"), " is an article about a cyclone that postdates the "
              "model's training data, a knowledge update. ", Strong("Science Q&A"), " is the Chemistry L-3 split of SciKnowEval, where "
              "the model has to reason with specialised knowledge rather than recall a fact."),
            P("Qwen3-4B-Instruct plays both student and teacher. We measure cost in ", Em("supervised tokens"), ", the number of "
              "response positions the loss is computed on. This is roughly proportional to compute. We use it instead of optimizer steps "
              "because on-policy rollouts are longer than off-policy ones, so an on-policy step costs more."),
            Figure(F.headline(), Cap("Test accuracy against cumulative supervised tokens. Drag the budget slider to compare methods at "
                                     "the same cost. Faint dots are raw evaluations; lines are smoothed."), cls="wide"),
            P("On all three tasks, SSD improves nearly as fast as off-policy early in training and then continues past the off-policy "
              "plateau to on-policy accuracy. It matches the on-policy plateau using ",
              Strong("44%"), ", ", Strong("34%"), " and ", Strong("57%"), " fewer supervised tokens respectively. On Science Q&A, "
              "the most reasoning-heavy task, it ends a few points above on-policy and roughly fifteen above off-policy."),
            P("This is consistent with our hypothesis that the useful signal is at positions where the document changes the "
              "prediction. Using the teacher only there keeps most of off-policy's token efficiency, and keeping the rest of the rollout "
              "on the student preserves on-policy's final accuracy.")),

        Sec("knob", "06", "Choosing τ",
            Div(Div(P("Since τ interpolates between off-policy and on-policy training, sweeping it traces the trade-off between them. At small τ "
                      "the teacher intervenes often: supervision is cheap but accuracy is capped, just like off-policy training. As τ "
                      "grows, more of each rollout comes from the student, accuracy improves, and the cost approaches that of "
                      "on-policy."),
                    P("Intermediate thresholds beat off-policy on accuracy while converging much "
                      "faster than on-policy, so SSD occupies the Pareto frontier between the two endpoints. With JSD as the switch, "
                      "τ between 0.2 and 0.5 is a good default. Hover over the points to see each run."),
                    cls="side-t"),
                Figure(F.tau_frontier(), Cap("Final accuracy vs supervised tokens for SSD across τ on Company Memo (JSD switch, 8 epochs). "
                                             "The curve is a guide to the eye."), cls="side-f"), cls="side")),

        Sec("curriculum", "07", "The teacher's share decreases during training",
            P("SSD does not need a schedule for how much the teacher participates. "
              "Early in training the student does not know the document's contents, the two models disagree at many positions, and the "
              "teacher writes a large share of every rollout: up to 40% of tokens at the lowest threshold. As the student absorbs the "
              "document, the disagreements shrink, the switch fires less often, and the rollouts become the student's own."),
            Figure(F.curriculum(), Cap("Training dynamics of SSD on Company Memo for several JSD thresholds. Left: the fraction of rollout "
                                       "tokens written by the teacher. Right: mean response length."), cls="wide"),
            P("Response length changes in a similar way. With a high threshold, the student keeps control for longer "
              "before divergence builds up enough to trigger the teacher, so early rollouts are long and erratic. As training goes on, "
              "the lengths settle and converge across thresholds. The teacher is used heavily while the student lacks the knowledge, "
              "and its share falls as the student learns, until training is close to on-policy.")),

        Sec("forgetting", "08", "Forgetting",
            P("Learning new knowledge often comes at the cost of old skills. SDFT showed that on-policy self-distillation forgets less "
              "than supervised fine-tuning. Since SSD keeps rollouts close to the student's own distribution, we expected it to inherit "
              "some of that advantage."),
            P("Qwen3-4B barely forgets anything under any method, probably because it has already been heavily post-trained on data "
              "that resembles the benchmarks. So we follow the SDFT protocol instead: fine-tune Qwen2.5-7B on SciKnowEval chemistry, "
              "then score in-domain accuracy against the average change on six general benchmarks (HellaSwag, HumanEval, IFEval, "
              "MMLU, TruthfulQA and Winogrande)."),
            Div(Figure(F.forgetting(), Cap("In-domain SciQA accuracy against the mean change on six general benchmarks. Error bars: "
                                           "95% CI."), cls="side-f"),
                Div(P("The off-policy methods, SFT and FKL, learn the new skill but give up about 6.6 points elsewhere. On-policy SDFT "
                      "forgets noticeably less, at −4.5."),
                    P("SSD reaches the ", Strong("best SciQA accuracy (71.6)"), " with the ",
                      Strong("least forgetting (−1.4)"), ", while using ", Strong("22% fewer supervised tokens"), " than SDFT. "
                      "In this setting it is better than both off- and on-policy distillation on all three measures."), cls="side-t"),
                cls="side rev")),

        Sec("routing", "09", "Switching at inference time",
            P("The switch can also be applied at inference, without any training. The teacher gets the question plus its ground-truth answer, the student gets only "
              "the question, and at each step the JSD between them decides who emits the next token. We then measure accuracy "
              "against the share of tokens that come from the teacher."),
            Figure(F.routing(), Cap("JSD-routed decoding with no weight updates, on 507 SciKnowEval chemistry questions with Qwen3-4B-Instruct. "
                                    "Right: the share of tokens emitted by the teacher."), cls="narrow"),
            P("On its own the student gets 13.8% right. Routing ", Strong("15.7%"), " of tokens to the teacher lifts accuracy to "
              "74.0%, within about six points of the pure teacher's 80.3%. Even at τ = 0.5, with fewer than 3% teacher tokens, accuracy "
              "is almost four times the student's. Answers also get shorter, because the teacher's interventions pull the student out "
              "of the long, looping reasoning it produces on its own."),
            P("This supports the idea behind SSD: much of the teacher's advantage comes from a small number of tokens, and the "
              "divergence between the two distributions identifies them.")),

        Section(Div(Span("", cls="num"), H2("Cite"), cls="sec-h"),
                Div(Button("copy", cls="copy", type="button"), Pre(Code(BIBTEX), cls="bib"), cls="bibwrap"), id="cite"),
    )


def nav():
    items = [("idea", "Idea"), ("why", "Why"), ("inflection", "Inflection"), ("method", "Method"), ("results", "Results"),
             ("knob", "τ"), ("curriculum", "Teacher share"), ("forgetting", "Forgetting"), ("routing", "Inference"), ("cite", "Cite")]
    return Nav(A("SSD", href="#top", cls="brand"), Div(*[A(t, href=f"#{i}", data_sec=i) for i, t in items], cls="nav-l"),
               Div(cls="progress"), cls="topnav")


CAPTURE = {"method": MethodFigure, "fork": F.fork, "signal": F.signal, "headline": F.headline,
           "tau_frontier": F.tau_frontier, "curriculum": F.curriculum, "forgetting": F.forgetting, "routing": F.routing}


@rt
def index(capture: str = ""):
    if capture in CAPTURE:
        return Title(f"SSD · {capture}"), Main(CAPTURE[capture](), cls=f"capture-main cap-{capture}", data_capture=capture)
    return (Title("Speculative Self-Distillation"), Meta(name="description", content=DESC),
            nav(), Main(hero(), tldr(), *body(), cls="page", id="top"),
            Footer(Div(*[Img(src=s, alt=a, cls="logo") for s, a in LOGOS.values()], cls="foot-logos"),
                   P("Speculative Self-Distillation · Stanford University & ETH Zürich · 2026"), cls="foot"))


serve(port=5001, reload=False)
