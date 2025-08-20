"""
共通ユーティリティ関数
"""
import os
import re
import logging
import structlog
from datetime import datetime
from typing import Optional, Dict, Any
from dateutil import parser

def setup_logging(log_level: str = "INFO", log_file: str = "receipt_processor.log"):
    """ログ設定の初期化"""
    # structlogの設定
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # ファイルハンドラーの設定
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(getattr(logging, log_level.upper()))
    
    # コンソールハンドラーの設定
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    
    # フォーマッターの設定
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # ルートロガーの設定
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return structlog.get_logger()

def extract_date_from_text(text: str) -> Optional[datetime]:
    """
    OCRテキストから日付を抽出する
    
    Args:
        text: OCRで抽出されたテキスト
        
    Returns:
        Optional[datetime]: 抽出された日付、見つからない場合はNone
    """
    # 日付パターンの定義
    date_patterns = [
        r'(\d{4})[年\-/](\d{1,2})[月\-/](\d{1,2})[日]?',  # 2024年1月1日, 2024-01-01
        r'(\d{1,2})[月\-/](\d{1,2})[日]?',  # 1月1日, 01-01
        r'(\d{4})[年\-/](\d{1,2})[月\-/](\d{1,2})',  # 2024年1月1, 2024-01-01
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                if len(match.groups()) == 3:
                    year, month, day = match.groups()
                    # 年が2桁の場合は20xx年と仮定
                    if len(year) == 2:
                        year = f"20{year}"
                    return datetime(int(year), int(month), int(day))
                elif len(match.groups()) == 2:
                    month, day = match.groups()
                    # 年が指定されていない場合は現在の年を使用
                    current_year = datetime.now().year
                    return datetime(current_year, int(month), int(day))
            except (ValueError, TypeError):
                continue
    
    return None

def extract_amount_from_text(text: str) -> Optional[float]:
    """
    OCRテキストから金額を抽出する
    
    Args:
        text: OCRで抽出されたテキスト
        
    Returns:
        Optional[float]: 抽出された金額、見つからない場合はNone
    """
    # 金額パターンの定義
    amount_patterns = [
        r'合計[：:]\s*([0-9,]+)',  # 合計: 1,000
        r'合計\s*([0-9,]+)',  # 合計 1,000
        r'税込[：:]\s*([0-9,]+)',  # 税込: 1,000
        r'税込\s*([0-9,]+)',  # 税込 1,000
        r'([0-9,]+)\s*円',  # 1,000円
        r'¥\s*([0-9,]+)',  # ¥ 1,000
        r'([0-9,]+)',  # 1,000
    ]
    
    for pattern in amount_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                amount_str = match.group(1).replace(',', '')
                return float(amount_str)
            except (ValueError, TypeError):
                continue
    
    return None

def extract_store_name_from_text(text: str) -> Optional[str]:
    """
    テキストから店舗名を抽出する（簡潔で実用的な店舗名）
    
    Args:
        text: 店舗名テキスト
        
    Returns:
        Optional[str]: 抽出された店舗名、見つからない場合はNone
    """
    if not text:
        return None
    
    store_name = text.strip()
    
    # 特定の店舗名パターンを優先的に抽出
    known_patterns = {
        r'apollo\s*station': 'apollo',
        r'apollostation': 'apollo', 
        r'エネオス|eneos': 'エネオス',
        r'ファミリーマート|familymart': 'ファミマ',
        r'セブンイレブン|7-eleven': 'セブン',
        r'ローソン|lawson': 'ローソン',
        r'マクドナルド|mcdonald': 'マック',
        r'スターバックス|starbucks': 'スタバ',
        r'dcm|ホームセンター': 'DCM',
        r'ダイソー|daiso': 'ダイソー',
        r'セリア|seria': 'セリア',
        r'ヨドバシ': 'ヨドバシ',
        r'ビックカメラ': 'ビック',
        r'ヤマダ電機': 'ヤマダ',
    }
    
    # 既知パターンに一致するかチェック（大文字小文字区別なし）
    text_lower = store_name.lower()
    for pattern, short_name in known_patterns.items():
        if re.search(pattern, text_lower):
            return short_name
    
    # 都道府県名を除去
    prefectures = ['北海道', '青森県', '岩手県', '宮城県', '秋田県', '山形県', '福島県',
                   '茨城県', '栃木県', '群馬県', '埼玉県', '千葉県', '東京都', '神奈川県',
                   '新潟県', '富山県', '石川県', '福井県', '山梨県', '長野県', '岐阜県',
                   '静岡県', '愛知県', '三重県', '滋賀県', '京都府', '大阪府', '兵庫県',
                   '奈良県', '和歌山県', '鳥取県', '島根県', '岡山県', '広島県', '山口県',
                   '徳島県', '香川県', '愛媛県', '高知県', '福岡県', '佐賀県', '長崎県',
                   '熊本県', '大分県', '宮崎県', '鹿児島県', '沖縄県']
    
    for prefecture in prefectures:
        if prefecture in store_name:
            # 都道府県名以降を除去
            store_name = store_name.split(prefecture)[0].strip()
            break
    
    # 住所パターンを除去
    store_name = re.sub(r'\d+[丁目番地号-]\d*', '', store_name)
    store_name = re.sub(r'[0-9]+[-−ー][0-9]+', '', store_name)
    
    # 法人格を除去
    store_name = re.sub(r'株式会社|有限会社|合同会社|一般社団法人|公益社団法人', '', store_name)
    
    # 不要な記号を除去
    store_name = re.sub(r'[【】\(\)（）\[\]「」]', '', store_name)
    
    # 数字のみの部分を除去
    store_name = re.sub(r'\s*\d+\s*', ' ', store_name)
    
    # 前後の空白を除去し、複数の空白を単一に
    store_name = re.sub(r'\s+', ' ', store_name.strip())
    
    # 短すぎる場合は元のテキストの最初の単語を使用
    if len(store_name) < 2:
        words = text.split()
        if words:
            return words[0][:10]  # 最大10文字
    
    # 最大10文字に制限
    return store_name[:10] if store_name else None

def generate_title(account_item: str, amount: Optional[float] = None) -> str:
    """
    タイトルを生成する（勘定科目+金額）
    
    Args:
        account_item: 勘定科目
        amount: 金額（オプション）
        
    Returns:
        str: 生成されたタイトル
    """
    # 金額がある場合は勘定科目+金額
    if amount:
        amount_str = f"¥{int(amount):,}"
        return f"{account_item} {amount_str}"
    else:
        return account_item

def get_year_month_folder_path(date: datetime) -> str:
    """
    年度・月度フォルダパスを生成する
    
    Args:
        date: 日付
        
    Returns:
        str: フォルダパス（例: /2025/08/）
    """
    year = date.year
    month = date.month
    return f"/{year}/{month:02d}/"

def validate_file_extension(filename: str, supported_formats: list) -> bool:
    """
    ファイル拡張子の妥当性をチェックする
    
    Args:
        filename: ファイル名
        supported_formats: サポートされている拡張子のリスト
        
    Returns:
        bool: 妥当な場合はTrue
    """
    _, ext = os.path.splitext(filename.lower())
    return ext in supported_formats

def sanitize_filename(filename: str) -> str:
    """
    ファイル名をサニタイズする
    
    Args:
        filename: 元のファイル名
        
    Returns:
        str: サニタイズされたファイル名
    """
    # 危険な文字を除去・置換
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = re.sub(r'\s+', '_', filename)
    return filename.strip('_.')

def create_processing_metadata(file_path: str, page_number: Optional[int] = None) -> Dict[str, Any]:
    """
    処理メタデータを作成する
    
    Args:
        file_path: ファイルパス
        page_number: ページ番号（PDFの場合）
        
    Returns:
        Dict[str, Any]: メタデータ
    """
    metadata = {
        'original_filename': os.path.basename(file_path),
        'file_size': os.path.getsize(file_path),
        'file_extension': os.path.splitext(file_path)[1].lower(),
        'processing_timestamp': datetime.now().isoformat(),
    }
    
    if page_number is not None:
        metadata['page_number'] = page_number
    
    return metadata
