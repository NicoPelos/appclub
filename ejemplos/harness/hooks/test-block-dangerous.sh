#!/usr/bin/env bash
# Prueba el hook con casos que deben bloquear (deny), pedir confirmación (ask) y pasar (pass).
HOOK="$(cd "$(dirname "$0")" && pwd)/block-dangerous.sh"
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
G="git -c user.email=t@t -c user.name=t"
(cd "$T" && mkdir rmain rfeat && cd rmain && git init -q -b main && $G commit -q --allow-empty -m i)
(cd "$T/rfeat" && git init -q -b main && $G commit -q --allow-empty -m i && git checkout -q -b feature/x)
fail=0; total=0
classify() { # $1=json  -> deny|ask|pass|other
  local out code
  out=$(printf '%s' "$1" | bash "$HOOK" 2>/dev/null); code=$?
  if [ $code -eq 2 ]; then echo deny
  elif [ $code -eq 0 ] && grep -q '"permissionDecision": "ask"' <<<"$out"; then echo ask
  elif [ $code -eq 0 ] && [ -z "$out" ]; then echo pass
  else echo "other(code=$code)"; fi
}
bash_case() { # expect cwd command
  total=$((total+1))
  local j; j=$(jq -n --arg c "$3" --arg d "$2" '{tool_name:"Bash",cwd:$d,tool_input:{command:$c}}')
  local got; got=$(classify "$j")
  if [ "$got" = "$1" ]; then echo "  ok    [$1] $3"; else echo "  FALLA [esperado $1, dio $got] $3"; fail=$((fail+1)); fi
}
file_case() { # expect tool path
  total=$((total+1))
  local j; j=$(jq -n --arg t "$2" --arg p "$3" '{tool_name:$t,cwd:"/x",tool_input:{file_path:$p}}')
  local got; got=$(classify "$j")
  if [ "$got" = "$1" ]; then echo "  ok    [$1] $2 $3"; else echo "  FALLA [esperado $1, dio $got] $2 $3"; fail=$((fail+1)); fi
}
M="$T/rmain"; F="$T/rfeat"
echo "== git push =="
bash_case deny "$M" 'git push --force origin main'
bash_case deny "$M" 'git push -f origin main'
bash_case deny "$M" 'git push origin +main'
bash_case deny "$M" 'git push origin HEAD:main --force'
bash_case deny "$M" 'git push --force origin production'
bash_case deny "$M" 'git push -fu origin master'
bash_case deny "$M" 'cd x && git push --force origin main'
bash_case deny "$M" 'git push --force'
bash_case deny "$F" "git -C $M push --force"
bash_case ask  "$M" 'git push --force-with-lease origin main'
bash_case pass "$F" 'git push --force'
bash_case pass "$F" 'git push --force origin feature/x'
bash_case pass "$F" 'git push -f origin feature/x'
bash_case pass "$M" 'git push --force-with-lease origin feature/x'
bash_case pass "$M" 'git push origin main'
bash_case pass "$M" 'git push origin feature/main-menu'
bash_case pass "$M" 'npm test'
echo "== .env por shell =="
bash_case deny "$M" 'echo SECRET=1 >> .env'
bash_case deny "$M" "sed -i 's/a/b/' .env"
bash_case deny "$M" 'rm .env'
bash_case deny "$M" 'cp .env.example .env'
bash_case deny "$M" 'tee .env <<< x'
bash_case pass "$M" 'cat .env.example'
bash_case pass "$M" 'cp .env.example .env.example.bak'
bash_case pass "$M" 'echo hola > notas.txt'
echo "== .env por Edit/Write =="
file_case deny Edit  /repo/.env
file_case deny Write /repo/.env.local
file_case deny Edit  /repo/.env.staging.local
file_case pass Edit  /repo/.env.example
file_case pass Edit  /repo/.env.production
file_case pass Edit  /repo/src/app.js
echo "== builds por ssh (Raspi) =="
bash_case deny "$M" 'ssh pi "cd web && npx vite build"'
bash_case deny "$M" 'ssh pi "cd web && npm run build"'
bash_case deny "$M" 'ssh pi "npm ci"'
bash_case deny "$M" 'ssh pi "docker compose build"'
bash_case deny "$M" 'ssh pi "docker compose build web"'
bash_case deny "$M" 'ssh pi "docker compose build app web"'
bash_case deny "$M" 'ssh pi "cd /srv/gradle-app && ./gradlew assembleRelease"'
bash_case pass "$M" 'ssh pi "docker compose build app"'
bash_case pass "$M" 'ssh pi "cd x && docker compose build app && docker compose up -d app"'
bash_case pass "$M" 'ssh pi "npm ci --omit=dev"'
bash_case pass "$M" 'ssh pi "docker compose up -d app"'
bash_case pass "$M" 'npm run build'
echo "== escrituras a Mongo por ssh / docker exec =="
bash_case ask  "$M" "ssh pi \"docker exec mongo mongosh appcarc --eval \\\"db.users.deleteOne({email:'a'})\\\"\""
bash_case ask  "$M" "docker exec mongo mongosh appcarc --eval 'db.socios.updateMany({}, {})'"
bash_case pass "$M" "ssh pi \"docker exec mongo mongosh appcarc --eval 'db.users.find()'\""
bash_case pass "$M" "ssh pi \"docker exec mongo mongosh appcarc --eval 'db.socios.countDocuments({})'\""
echo "== otras herramientas =="
total=$((total+1)); got=$(classify '{"tool_name":"Read","cwd":"/x","tool_input":{"file_path":"/repo/.env"}}'); [ "$got" = pass ] && echo "  ok    [pass] Read .env (no se frena la lectura)" || { echo "  FALLA Read dio $got"; fail=$((fail+1)); }
total=$((total+1)); got=$(classify 'esto no es json'); [ "$got" = pass ] && echo "  ok    [pass] entrada inválida no rompe" || { echo "  nota: entrada inválida => $got"; }
echo; echo "Resultado: $((total-fail))/$total OK"; exit $fail
