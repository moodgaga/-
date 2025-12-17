# Скрипт для запуска backend и frontend одновременно

echo "🚀 Ззапуск всего"
echo ""

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Функция для очистки при выходе
cleanup() {
    echo ""
    echo "🛑 остановка"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit
}

trap cleanup SIGINT SIGTERM

# Проверка backend
if [ ! -d "backend" ]; then
    echo "❌ Папка backend не найдена"
    exit 1
fi

# Проверка frontend
if [ ! -f "index.html" ]; then
    echo "❌ index.html не найден"
    exit 1
fi

# Запуск backend
echo -e "${BLUE}📦 Запуск backend ${NC}"
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000 > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Ожидание запуска backend
sleep 3

# Проверка backend
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${YELLOW}⚠️  Backend не отвечает, но продолжаем...${NC}"
else
    echo -e "${GREEN}✅ Backend запущен на http://localhost:8000${NC}"
fi

# Запуск frontend
echo -e "${BLUE}🌐 Запуск frontend сервера...${NC}"
python3 -m http.server 8080 > frontend.log 2>&1 &
FRONTEND_PID=$!

sleep 1
echo -e "${GREEN}✅ Frontend запущен на http://localhost:8080${NC}"
echo ""
echo "=" | head -c 60
echo ""
echo -e "${GREEN}✅ Всезапущено!${NC}"
echo ""
echo "📝 Backend API:  http://localhost:8000"
echo "📝 Backend Docs: http://localhost:8000/docs"
echo "📝 Frontend:     http://localhost:8080"
echo ""
echo "📋 Логи backend:  tail -f backend.log"
echo "📋 Логи frontend: tail -f frontend.log"
echo ""
echo "Для остановки нажмите Ctrl+C"
echo "=" | head -c 60
echo ""

# Ожидание
wait

