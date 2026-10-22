# Prácticas para trabajar con IA

Lo que aprendí armando este setup. Corto a propósito.

## El orden para aprender
1. **Domina un solo agente** (Claude Code) en un proyecto real antes de coordinar varios.
2. **Dale contexto con un `CLAUDE.md`** por proyecto: cómo correr y probar, qué no tocar y
   tus convenciones. Pesa más que cualquier "prompt mágico". Ejemplo:
   [ejemplos/modelo-dual/CLAUDE.md](ejemplos/modelo-dual/CLAUDE.md).
3. **Conecta MCPs que de verdad uses** (GitHub, Notion…). Menos de 10 activos por proyecto:
   cada uno ocupa contexto.
4. **Crea roles (subagentes)** cuando sientas la necesidad, no antes.
5. **Coordina varias IAs** (Codex, Gemini) al final: lo práctico es que una sea la principal
   y las otras den una segunda opinión, comunicándose por archivos y git, no por chat.

## El ciclo con los comandos
1. `/explicar` la parte que vas a cambiar.
2. `/planear` el cambio y aprueba (o corrige) el plan.
3. Implementa, a mano, con Claude o con `/tdd`.
4. `/revisar-codigo` y, si toca datos sensibles, `/seguridad`.
5. Corrige lo que reporten y haz commit.

"Un agente escribe y otro revisa": un revisor con una sola tarea encuentra lo que se le pasó
al que escribió. En su primera prueba encontró dos bugs reales de pérdida de datos.

## Reglas que funcionan
- **Los roles que solo revisan no tienen permiso de escribir** (`tools: Read, Grep, Glob, Bash`).
- **Filtro de confianza:** el revisor reporta solo lo que tiene más del 80% de certeza, con
  archivo, línea y un caso concreto que falla. Una revisión sin hallazgos es válida.
- **Verifica antes de arreglar:** comprueba en el código los hallazgos críticos y altos; un
  agente también se equivoca.
- **No instales setups ajenos completos.** Toma piezas sueltas y adáptalas a tu stack. Los
  agentes de aquí salieron de
  [everything-claude-code](https://github.com/affaan-m/everything-claude-code) (71 agentes,
  casi todos para JavaScript) y hubo que reescribirlos.
- **Cuidado con los nombres:** un comando global puede chocar con uno del proyecto (por eso el
  revisor de código es `/revisar-codigo` y no `/revisar`).
- **Un proyecto puede tener su propio agente** con el mismo nombre que uno global para
  especializarlo, como el `revisor` de
  [ejemplos/modelo-dual](ejemplos/modelo-dual/.claude/agents/revisor.md).
- **Los hooks ejecutan código solo:** léelos antes de instalarlos.
