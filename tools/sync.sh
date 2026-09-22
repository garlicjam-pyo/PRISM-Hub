#!/usr/bin/env bash
# tools/sync.sh -- 두 컴퓨터 간 작업 동기화 도우미 (macOS/Linux)
# 사용: 작업 시작 전  ./tools/sync.sh start ;  작업 끝난 뒤  ./tools/sync.sh end "메시지"
set -e; cd "$(dirname "$0")/.."
case "${1:-start}" in
  start)
    git fetch origin
    if [ -n "$(git status --porcelain)" ]; then echo "주의: 커밋되지 않은 변경이 있습니다. 먼저 end 로 커밋하세요."; git status --short; exit 1; fi
    git pull --ff-only origin main; echo "동기화 완료: $(git log -1 --oneline)";;
  end)
    msg="${2:-$(read -p '커밋 메시지: ' m; echo "$m")}"
    git add -A; git commit -m "$msg"; git pull --rebase origin main; git push origin main; echo "푸시 완료: $(git log -1 --oneline)";;
  *) echo "mode 는 start 또는 end";;
esac
