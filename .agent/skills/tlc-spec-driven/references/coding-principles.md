# Coding Principles

Behavioral bias, not checklist. Read before every implementation.

---

## Before Coding

- State assumptions explicitly. If uncertain, ask.
- Multiple interpretations exist? Present all-don't pick silently.
- Simpler approach exists? Say so. Push back when warranted.
- Something unclear? Stop. Name what's confusing. Ask.
- User's approach seems wrong? Disagree honestly. Don't be sycophantic.

---

## During Implementation

### Simplicity

- No features beyond what was asked
- No abstractions for single-use code
- No "flexibility" or "configurability" not requested
- No error handling for impossible scenarios
- 200 lines that could be 50? Rewrite it.

### Surgical Changes

- Don't "improve" adjacent code, comments, or formatting
- Don't refactor things that aren't broken
- Match existing style, even if you'd do differently
- Unrelated dead code noticed? Mention it-don't delete it
- Remove ONLY imports/variables/functions YOUR changes orphaned
- Don't remove pre-existing dead code unless asked

### Test Integrity

- NEVER weaken an existing test assertion to make it pass
- NEVER delete a test to reduce failure count
- NEVER use the test framework's skip/disable/pending mechanism to bypass a failing test
- NEVER modify a task's tests afterward to make the implementation pass
- If a test is genuinely wrong, STOP and confirm with the user before changing it
- Tests are the spec - implementation conforms to tests, not the other way around

### Goal-Driven

- Transform vague tasks into verifiable goals
- Multi-step work? State brief plan with verify checkpoints
- Every changed line must trace directly to user's request

---

## After Each Change

Ask: "Would senior engineer call this overcomplicated?"
If yes → simplify before proceeding.

---

## Writing Voice (specs, ADRs, reports, commits, summaries)

The artifacts this skill produces should read like an engineer wrote them, not like generated boilerplate.

- **Lead with the verdict.** Validation reports and chat summaries open with PASS/FAIL and the concrete finding, not a warm-up paragraph.
- **Decisions are definitive.** An ADR or a recorded decision states what was chosen: "we will", not "we might" or "we should probably". If it still hedges, it is not a decision yet.
- **Cut filler and mechanical hedging.** Drop "it is worth noting", "as you can see", "in order to", and reflexive "may/might/could" on claims you are actually sure about. Reserve hedging for genuine uncertainty.
- **One idea per sentence; short sentences.** Prefer the plain verb over the nominalization ("evaluated", not "performed an evaluation of"). Keep subject-verb-object near the front.
- **Do not announce the phase.** Produce the artifact; do not narrate "I will now run Specify."
- **Avoid the em dash as a default connector.** A comma, colon, or two sentences usually read cleaner.
- **Editorial guidelines for Portuguese documentation:**
  - Prefira frases curtas e objetivas.
  - Use termos técnicos apenas quando necessários, sem jargão vazio para inflar o texto.
  - Elimine adjetivos promocionais e afirmações grandiosas.
  - Evite clichês de texto gerado por IA: "pilares fundamentais", "regra de ouro", "disciplina rigorosa e auditável", "não-negociável", "robusto e escalável", "de ponta a ponta" ou similares, quando vazios.
  - Não repita a mesma informação em seções diferentes do mesmo documento.
  - Elimine introduções longas que apenas anunciam o que será apresentado a seguir.
  - Explique o que o componente faz, por que existe e quais são suas responsabilidades.
  - Mantenha tom impessoal e profissional.
  - **A documentação deve descrever o projeto, não a interação com o usuário:** Não registrar mensagens, confirmações, solicitações, autorizações ou etapas de conversa nos documentos técnicos (evitar "aguardando confirmação do usuário", "o usuário deverá validar", "solicitar autorização", "no chat"). Quando uma ação externa for necessária, registrar apenas seu estado objetivo e o critério técnico correspondente (ex.: "homologação manual não executada", "validação manual pendente").
  - Preserve estritamente a distinção entre requisitos (o que o sistema deve fazer), decisões arquiteturais (como foi desenhado), procedimentos (como operar ou testar) e resultados (evidências observadas).

None of this means dumbing down the content - only the prose carrying it.
