# Создайте файл app/modules/crypto_trading_system.py

#!/usr/bin/env python3
"""
₿ CRYPTO TRADING SYSTEM v4.0
Полная система криптовалютных курсов через CoinGecko API
"""

import logging
import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from decimal import Decimal
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class CryptoPrice:
    symbol: str
    name: str
    current_price: float
    price_change_24h: float
    price_change_percentage_24h: float
    market_cap: float
    volume_24h: float
    last_updated: datetime
    
    def get_price_emoji(self) -> str:
        """Возвращает эмодзи в зависимости от изменения цены"""
        if self.price_change_percentage_24h > 5:
            return "🚀"
        elif self.price_change_percentage_24h > 0:
            return "📈"
        elif self.price_change_percentage_24h < -5:
            return "💥"
        elif self.price_change_percentage_24h < 0:
            return "📉"
        else:
            return "➡️"

@dataclass
class Portfolio:
    user_id: int
    chat_id: int
    portfolio_name: str
    holdings: Dict[str, float]  # symbol -> amount
    created_at: datetime
    last_updated: datetime
    total_value_usd: float = 0.0
    daily_change_usd: float = 0.0
    daily_change_percent: float = 0.0

@dataclass
class PriceAlert:
    alert_id: str
    user_id: int
    chat_id: int
    symbol: str
    alert_type: str  # above, below, change_percent
    target_value: float
    current_value: float
    is_active: bool
    created_at: datetime
    triggered_at: Optional[datetime] = None

class CryptoTradingSystem:
    """₿ Система криптовалютной торговли"""
    
    def __init__(self, db_service, bot, config):
        self.db = db_service
        self.bot = bot
        self.config = config
        
        # CoinGecko API
        self.coingecko_base_url = "https://api.coingecko.com/api/v3"
        self.rate_limit_delay = 1.0  # Задержка между запросами
        
        # Кэш цен
        self.price_cache = {}
        self.cache_expiry = {}
        self.cache_duration = 60  # 1 минута
        
        # Активные портфели
        self.portfolios_cache = {}
        
        # Активные алерты
        self.active_alerts = {}
        
        # Поддерживаемые валюты
        self.supported_currencies = ["usd", "eur", "rub", "btc", "eth"]
        
        # Популярные криптовалюты
        self.popular_cryptos = {
            "bitcoin": "BTC",
            "ethereum": "ETH", 
            "binancecoin": "BNB",
            "cardano": "ADA",
            "solana": "SOL",
            "polkadot": "DOT",
            "dogecoin": "DOGE",
            "avalanche-2": "AVAX",
            "polygon": "MATIC",
            "chainlink": "LINK"
        }
        
        logger.info("₿ Crypto Trading System инициализирован")
    
    async def initialize(self):
        """Инициализация системы"""
        await self._create_tables()
        await self._load_active_alerts()
        
        # Запускаем фоновые задачи
        asyncio.create_task(self._price_monitoring_loop())
        asyncio.create_task(self._alert_checking_loop())
        asyncio.create_task(self._cleanup_old_data())
    
    async def _create_tables(self):
        """Создает таблицы для крипто-системы"""
        
        # История цен
        await self.db.execute('''
        CREATE TABLE IF NOT EXISTS crypto_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            name TEXT NOT NULL,
            price_usd REAL NOT NULL,
            price_change_24h REAL,
            price_change_percent_24h REAL,
            market_cap REAL,
            volume_24h REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            INDEX(symbol, timestamp),
            INDEX(timestamp)
        )
        ''')
        
        # Пользовательские портфели
        await self.db.execute('''
        CREATE TABLE IF NOT EXISTS crypto_portfolios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            chat_id INTEGER NOT NULL,
            portfolio_name TEXT NOT NULL,
            holdings TEXT NOT NULL,  -- JSON
            total_value_usd REAL DEFAULT 0.0,
            daily_change_usd REAL DEFAULT 0.0,
            daily_change_percent REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            UNIQUE(user_id, chat_id, portfolio_name),
            INDEX(user_id, chat_id)
        )
        ''')
        
        # Алерты цен
        await self.db.execute('''
        CREATE TABLE IF NOT EXISTS price_alerts (
            alert_id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            chat_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            target_value REAL NOT NULL,
            current_value REAL,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            triggered_at TIMESTAMP,
            
            INDEX(user_id, chat_id),
            INDEX(symbol),
            INDEX(is_active)
        )
        ''')
        
        # История торговых операций
        await self.db.execute('''
        CREATE TABLE IF NOT EXISTS trading_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            chat_id INTEGER NOT NULL,
            portfolio_name TEXT NOT NULL,
            operation_type TEXT NOT NULL,  -- buy, sell
            symbol TEXT NOT NULL,
            amount REAL NOT NULL,
            price_usd REAL NOT NULL,
            total_usd REAL NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            INDEX(user_id, chat_id),
            INDEX(symbol),
            INDEX(timestamp)
        )
        ''')
        
        # Подписки на обновления
        await self.db.execute('''
        CREATE TABLE IF NOT EXISTS crypto_subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            chat_id INTEGER NOT NULL,
            symbols TEXT NOT NULL,  -- JSON array
            update_frequency INTEGER DEFAULT 3600,  -- seconds
            last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            
            UNIQUE(user_id, chat_id),
            INDEX(is_active),
            INDEX(last_update)
        )
        ''')
    
    async def get_crypto_price(self, symbol: str, vs_currency: str = "usd") -> Optional[CryptoPrice]:
        """💰 Получает текущую цену криптовалюты"""
        
        try:
            # Нормализуем символ
            symbol = symbol.lower()
            crypto_id = self._get_crypto_id(symbol)
            
            if not crypto_id:
                return None
            
            # Проверяем кэш
            cache_key = f"{crypto_id}_{vs_currency}"
            if self._is_cache_valid(cache_key):
                return self.price_cache[cache_key]
            
            # Запрашиваем данные из CoinGecko
            url = f"{self.coingecko_base_url}/simple/price"
            params = {
                'ids': crypto_id,
                'vs_currencies': vs_currency,
                'include_24hr_change': 'true',
                'include_market_cap': 'true',
                'include_24hr_vol': 'true'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if crypto_id in data:
                            crypto_data = data[crypto_id]
                            
                            price_obj = CryptoPrice(
                                symbol=symbol.upper(),
                                name=self._get_crypto_name(crypto_id),
                                current_price=crypto_data[vs_currency],
                                price_change_24h=crypto_data.get(f'{vs_currency}_24h_change', 0),
                                price_change_percentage_24h=crypto_data.get(f'{vs_currency}_24h_change', 0),
                                market_cap=crypto_data.get(f'{vs_currency}_market_cap', 0),
                                volume_24h=crypto_data.get(f'{vs_currency}_24h_vol', 0),
                                last_updated=datetime.now()
                            )
                            
                            # Сохраняем в кэш
                            self.price_cache[cache_key] = price_obj
                            self.cache_expiry[cache_key] = datetime.now() + timedelta(seconds=self.cache_duration)
                            
                            # Сохраняем в БД для истории
                            await self._save_price_history(price_obj, vs_currency)
                            
                            return price_obj
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения цены {symbol}: {e}")
            return None
    
    async def get_multiple_prices(self, symbols: List[str], vs_currency: str = "usd") -> List[CryptoPrice]:
        """📊 Получает цены нескольких криптовалют"""
        
        try:
            # Преобразуем символы в ID
            crypto_ids = []
            symbol_to_id = {}
            
            for symbol in symbols:
                crypto_id = self._get_crypto_id(symbol.lower())
                if crypto_id:
                    crypto_ids.append(crypto_id)
                    symbol_to_id[crypto_id] = symbol.upper()
            
            if not crypto_ids:
                return []
            
            # Запрашиваем данные
            url = f"{self.coingecko_base_url}/simple/price"
            params = {
                'ids': ','.join(crypto_ids),
                'vs_currencies': vs_currency,
                'include_24hr_change': 'true',
                'include_market_cap': 'true',
                'include_24hr_vol': 'true'
            }
            
            prices = []
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for crypto_id, crypto_data in data.items():
                            if crypto_id in symbol_to_id:
                                price_obj = CryptoPrice(
                                    symbol=symbol_to_id[crypto_id],
                                    name=self._get_crypto_name(crypto_id),
                                    current_price=crypto_data[vs_currency],
                                    price_change_24h=crypto_data.get(f'{vs_currency}_24h_change', 0),
                                    price_change_percentage_24h=crypto_data.get(f'{vs_currency}_24h_change', 0),
                                    market_cap=crypto_data.get(f'{vs_currency}_market_cap', 0),
                                    volume_24h=crypto_data.get(f'{vs_currency}_24h_vol', 0),
                                    last_updated=datetime.now()
                                )
                                
                                prices.append(price_obj)
                                
                                # Сохраняем в кэш
                                cache_key = f"{crypto_id}_{vs_currency}"
                                self.price_cache[cache_key] = price_obj
                                self.cache_expiry[cache_key] = datetime.now() + timedelta(seconds=self.cache_duration)
            
            return prices
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения множественных цен: {e}")
            return []
    
    async def create_portfolio(self, user_id: int, chat_id: int, 
                             portfolio_name: str) -> Tuple[bool, str]:
        """📊 Создает новый портфель"""
        
        try:
            # Проверяем существование
            existing = await self.db.fetch_one('''
            SELECT id FROM crypto_portfolios 
            WHERE user_id = ? AND chat_id = ? AND portfolio_name = ?
            ''', (user_id, chat_id, portfolio_name))
            
            if existing:
                return False, f"❌ Портфель '{portfolio_name}' уже существует"
            
            # Создаем портфель
            await self.db.execute('''
            INSERT INTO crypto_portfolios (user_id, chat_id, portfolio_name, holdings)
            VALUES (?, ?, ?, ?)
            ''', (user_id, chat_id, portfolio_name, json.dumps({})))
            
            return True, f"✅ Портфель '{portfolio_name}' создан!"
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания портфеля: {e}")
            return False, f"❌ Ошибка: {str(e)}"
    
    async def add_to_portfolio(self, user_id: int, chat_id: int, portfolio_name: str,
                             symbol: str, amount: float) -> Tuple[bool, str]:
        """➕ Добавляет криптовалюту в портфель"""
        
        try:
            # Получаем портфель
            portfolio_data = await self.db.fetch_one('''
            SELECT holdings FROM crypto_portfolios 
            WHERE user_id = ? AND chat_id = ? AND portfolio_name = ?
            ''', (user_id, chat_id, portfolio_name))
            
            if not portfolio_data:
                return False, f"❌ Портфель '{portfolio_name}' не найден"
            
            # Парсим holdings
            holdings = json.loads(portfolio_data[0])
            symbol_upper = symbol.upper()
            
            # Добавляем или обновляем
            if symbol_upper in holdings:
                holdings[symbol_upper] += amount
            else:
                holdings[symbol_upper] = amount
            
            # Обновляем в БД
            await self.db.execute('''
            UPDATE crypto_portfolios 
            SET holdings = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND chat_id = ? AND portfolio_name = ?
            ''', (json.dumps(holdings), user_id, chat_id, portfolio_name))
            
            # Записываем в историю операций
            current_price = await self.get_crypto_price(symbol)
            if current_price:
                total_value = amount * current_price.current_price
                
                await self.db.execute('''
                INSERT INTO trading_history 
                (user_id, chat_id, portfolio_name, operation_type, symbol, amount, price_usd, total_usd)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, chat_id, portfolio_name, 'buy', symbol_upper, 
                      amount, current_price.current_price, total_value))
            
            # Обновляем кэш портфеля
            await self._update_portfolio_value(user_id, chat_id, portfolio_name)
            
            return True, f"✅ Добавлено {amount} {symbol_upper} в портфель '{portfolio_name}'"
            
        except Exception as e:
            logger.error(f"❌ Ошибка добавления в портфель: {e}")
            return False, f"❌ Ошибка: {str(e)}"
    
    async def get_portfolio_value(self, user_id: int, chat_id: int, 
                                portfolio_name: str) -> Optional[Portfolio]:
        """💼 Получает стоимость портфеля"""
        
        try:
            # Получаем портфель
            portfolio_data = await self.db.fetch_one('''
            SELECT holdings, total_value_usd, daily_change_usd, daily_change_percent, 
                   created_at, updated_at
            FROM crypto_portfolios 
            WHERE user_id = ? AND chat_id = ? AND portfolio_name = ?
            ''', (user_id, chat_id, portfolio_name))
            
            if not portfolio_data:
                return None
            
            holdings = json.loads(portfolio_data[0])
            
            if not holdings:
                return Portfolio(
                    user_id=user_id,
                    chat_id=chat_id,
                    portfolio_name=portfolio_name,
                    holdings=holdings,
                    created_at=datetime.fromisoformat(portfolio_data[4]),
                    last_updated=datetime.fromisoformat(portfolio_data[5]),
                    total_value_usd=0.0
                )
            
            # Получаем текущие цены
            symbols = list(holdings.keys())
            prices = await self.get_multiple_prices(symbols)
            
            total_value = 0.0
            for price_obj in prices:
                if price_obj.symbol in holdings:
                    amount = holdings[price_obj.symbol]
                    total_value += amount * price_obj.current_price
            
            return Portfolio(
                user_id=user_id,
                chat_id=chat_id,
                portfolio_name=portfolio_name,
                holdings=holdings,
                total_value_usd=total_value,
                daily_change_usd=portfolio_data[2] or 0.0,
                daily_change_percent=portfolio_data[3] or 0.0,
                created_at=datetime.fromisoformat(portfolio_data[4]),
                last_updated=datetime.fromisoformat(portfolio_data[5])
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения стоимости портфеля: {e}")
            return None
    
    async def create_price_alert(self, user_id: int, chat_id: int, symbol: str,
                               alert_type: str, target_value: float) -> Tuple[bool, str]:
        """🚨 Создает алерт на цену"""
        
        try:
            # Валидация
            if alert_type not in ['above', 'below', 'change_percent']:
                return False, "❌ Неверный тип алерта. Используйте: above, below, change_percent"
            
            # Получаем текущую цену
            current_price = await self.get_crypto_price(symbol)
            if not current_price:
                return False, f"❌ Криптовалюта {symbol} не найдена"
            
            # Создаем ID алерта
            alert_id = hashlib.md5(f"{user_id}_{chat_id}_{symbol}_{alert_type}_{target_value}_{datetime.now()}".encode()).hexdigest()
            
            # Сохраняем алерт
            await self.db.execute('''
            INSERT INTO price_alerts 
            (alert_id, user_id, chat_id, symbol, alert_type, target_value, current_value)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (alert_id, user_id, chat_id, symbol.upper(), alert_type, target_value, current_price.current_price))
            
            # Добавляем в активные алерты
            alert = PriceAlert(
                alert_id=alert_id,
                user_id=user_id,
                chat_id=chat_id,
                symbol=symbol.upper(),
                alert_type=alert_type,
                target_value=target_value,
                current_value=current_price.current_price,
                is_active=True,
                created_at=datetime.now()
            )
            
            self.active_alerts[alert_id] = alert
            
            # Формируем сообщение
            type_names = {
                'above': 'выше',
                'below': 'ниже', 
                'change_percent': 'изменение на'
            }
            
            type_name = type_names.get(alert_type, alert_type)
            
            return True, f"🚨 Алерт создан!\n\n📍 {symbol.upper()} {type_name} ${target_value:,.2f}\n💰 Текущая цена: ${current_price.current_price:,.2f}"
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания алерта: {e}")
            return False, f"❌ Ошибка: {str(e)}"
    
    async def format_price_message(self, price: CryptoPrice, vs_currency: str = "usd") -> str:
        """📝 Форматирует сообщение с ценой"""
        
        try:
            currency_symbols = {
                "usd": "$",
                "eur": "€", 
                "rub": "₽",
                "btc": "₿",
                "eth": "Ξ"
            }
            
            currency_symbol = currency_symbols.get(vs_currency, "$")
            
            message = f"{price.get_price_emoji()} **{price.name} ({price.symbol})**\n\n"
            message += f"💰 **Цена:** {currency_symbol}{price.current_price:,.8f}\n"
            
            # Изменение за 24 часа
            change_emoji = "🔴" if price.price_change_percentage_24h < 0 else "🟢"
            message += f"{change_emoji} **24ч:** {price.price_change_percentage_24h:+.2f}%"
            
            if price.price_change_24h != 0:
                message += f" ({currency_symbol}{price.price_change_24h:+,.2f})\n"
            else:
                message += "\n"
            
            # Дополнительная информация
            if price.market_cap > 0:
                message += f"📊 **Капитализация:** {currency_symbol}{price.market_cap:,.0f}\n"
            
            if price.volume_24h > 0:
                message += f"📈 **Объем 24ч:** {currency_symbol}{price.volume_24h:,.0f}\n"
            
            message += f"\n🕐 *Обновлено: {price.last_updated.strftime('%H:%M:%S')}*"
            
            return message
            
        except Exception as e:
            logger.error(f"❌ Ошибка форматирования сообщения: {e}")
            return f"❌ Ошибка отображения цены {price.symbol}"
    
    def _get_crypto_id(self, symbol: str) -> Optional[str]:
        """Получает ID криптовалюты для CoinGecko API"""
        
        # Поиск в популярных криптовалютах
        for crypto_id, crypto_symbol in self.popular_cryptos.items():
            if crypto_symbol.lower() == symbol.lower():
                return crypto_id
        
        # Если не найдено, пробуем использовать symbol как ID
        return symbol.lower()
    
    def _get_crypto_name(self, crypto_id: str) -> str:
        """Получает название криптовалюты"""
        
        names = {
            "bitcoin": "Bitcoin",
            "ethereum": "Ethereum",
            "binancecoin": "BNB",
            "cardano": "Cardano",
            "solana": "Solana",
            "polkadot": "Polkadot",
            "dogecoin": "Dogecoin"
        }
        
        return names.get(crypto_id, crypto_id.title())

# ЭКСПОРТ
__all__ = ["CryptoTradingSystem", "CryptoPrice", "Portfolio", "PriceAlert"]
