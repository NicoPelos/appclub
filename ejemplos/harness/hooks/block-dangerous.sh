#!/usr/bin/env bash
# PreToolUse: frena acciones peligrosas del agente.
#   exit 2        -> BLOQUEA (el mensaje de stderr vuelve al modelo)
#   JSON "ask"    -> pide confirmación al usuario
#   exit 0 mudo   -> sigue el flujo normal de permisos
# OJO: un `exit 1` NO bloquea nada. Para bloquear siempre `exit 2`.
# Requiere `jq`. Probar con: .claude/hooks/test-block-dangerous.sh

INPUT=$(cat)
TOOL=$(jq -r '.tool_name // empty' <<<"$INPUT")
CWD=$(jq -r '.cwd // empty' <<<"$INPUT")

deny() { echo "BLOQUEADO: $1" >&2; exit 2; }
ask() {
  jq -n --arg r "$1" '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"ask",permissionDecisionReason:$r}}'
  exit 0
}

is_protected() { case "$1" in main|master|production) return 0;; esac; return 1; }

# ---------- Edit / Write sobre archivos .env con secretos ----------
case "$TOOL" in
  Edit|Write|MultiEdit|NotebookEdit)
    F=$(jq -r '.tool_input.file_path // .tool_input.notebook_path // empty' <<<"$INPUT")
    B=$(basename -- "$F")
    case "$B" in
      .env|.env.local|.env.*.local)
        deny "no se edita $B desde el agente (tiene secretos). Pedile a Nico que lo cambie a mano. .env.example sí se puede editar." ;;
    esac
    exit 0 ;;
  Bash) ;;
  *) exit 0 ;;
esac

CMD=$(jq -r '.tool_input.command // empty' <<<"$INPUT")
CLEAN=$(tr -d "\"'" <<<"$CMD")          # sin comillas, para que los patrones sean simples
SEGS=$(sed -E 's/(&&|\|\||;|\|)/\n/g' <<<"$CLEAN")   # un comando por línea

# ---------- 1) git push --force a rama protegida ----------
while IFS= read -r seg; do
  grep -Eq '(^|[[:space:]])git[[:space:]]+(-C[[:space:]]+[^[:space:]]+[[:space:]]+)?push([[:space:]]|$)' <<<"$seg" || continue
  DIR="$CWD"
  C=$(sed -nE 's/.*git[[:space:]]+-C[[:space:]]+([^[:space:]]+)[[:space:]]+push.*/\1/p' <<<"$seg")
  [ -n "$C" ] && DIR="$C"
  read -ra T <<<"${seg#*push}"
  force=0; lease=0; pos=()
  for t in "${T[@]}"; do
    case "$t" in
      --force-with-lease*|--force-if-includes) lease=1 ;;
      --force|-f) force=1 ;;
      --*) ;;
      -*) [[ "$t" == *f* ]] && force=1 ;;
      +*) force=1; pos+=("$t") ;;
      *) pos+=("$t") ;;
    esac
  done
  [ $force -eq 0 ] && [ $lease -eq 0 ] && continue
  if [ ${#pos[@]} -ge 2 ]; then ref="${pos[1]}"; else ref=$(git -C "${DIR:-.}" rev-parse --abbrev-ref HEAD 2>/dev/null); fi
  ref="${ref#+}"; ref="${ref##*:}"; ref="${ref#refs/heads/}"
  if is_protected "$ref"; then
    if [ $force -eq 1 ]; then
      deny "force push a '$ref' (rama protegida). Si de verdad hace falta, que lo haga Nico a mano."
    else
      ask "--force-with-lease a '$ref' (rama protegida): reescribe el historial de esa rama. ¿Seguro?"
    fi
  fi
done <<<"$SEGS"

# ---------- 2) escribir/borrar .env desde el shell ----------
if grep -Eq '(>|\btee\b|\bsed[[:space:]]+-[a-zA-Z]*i|\brm\b|\bmv\b|\bcp\b|\btruncate\b)[^|;&]*(^|[[:space:]/=])\.env(\.local|\.[A-Za-z0-9_-]+\.local)?([[:space:]]|$)' <<<"$CLEAN"; then
  deny "no se escribe ni se borra un .env desde el shell (tiene secretos). Pedile a Nico que lo cambie a mano."
fi

# ---------- 3) builds pesados / comandos riesgosos por ssh (la Raspi se colgó dos veces) ----------
if grep -Eq '(^|[[:space:]])ssh[[:space:]]' <<<"$CLEAN"; then
  if grep -Eq 'vite[[:space:]]+build|npm[[:space:]]+run[[:space:]]+build|gradlew|\bgradle\b' <<<"$CLEAN"; then
    deny "builds de frontend/APK no se corren en la Raspi (la dejaron sin responder dos veces). Buildear en la PC y subir el resultado."
  fi
  if grep -Eq 'npm[[:space:]]+(ci|install)' <<<"$CLEAN" && ! grep -Eq -- '--omit=dev|--production' <<<"$CLEAN"; then
    deny "npm ci/install completo en la Raspi: solo con --omit=dev (backend). Los frontends se buildean en la PC."
  fi
  if grep -Eq 'docker([[:space:]]+compose|-compose)[[:space:]]+build' <<<"$CLEAN"; then
    AFTER=$(sed -nE 's/.*docker([[:space:]]+compose|-compose)[[:space:]]+build([[:space:]]+(.*))?$/\3/p' <<<"$CLEAN" | sed -E 's/(&&|\|\||;|\|).*//')
    svcs=0; bad=0
    for w in $AFTER; do case "$w" in -*) ;; *) svcs=$((svcs+1)); [ "$w" != "app" ] && bad=1 ;; esac; done
    if [ $svcs -eq 0 ] || [ $bad -eq 1 ]; then
      deny "en la Raspi solo se buildea el servicio 'app' (docker compose build app). Sin servicio construye todo, incluidos los frontends."
    fi
  fi
fi

# ---------- 4) escrituras directas a Mongo por ssh / docker exec ----------
if grep -Eq 'mongosh|mongorestore|(^|[[:space:]])mongo[[:space:]]' <<<"$CLEAN" \
   && grep -Eq '(^|[[:space:]])ssh[[:space:]]|docker[[:space:]]+(compose[[:space:]]+)?exec' <<<"$CLEAN" \
   && grep -Eq '\.(deleteOne|deleteMany|updateOne|updateMany|insertOne|insertMany|replaceOne|findOneAndUpdate|findOneAndDelete|findOneAndReplace|bulkWrite|drop|remove|dropDatabase|createIndex|dropIndex|renameCollection)\(|mongorestore' <<<"$CLEAN"; then
  ask "escritura directa en la base de producción (Mongo). ¿Confirmás que Nico la autorizó?"
fi

exit 0
