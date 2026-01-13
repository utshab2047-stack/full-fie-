# order_utils.py
# NEW VERSION - HTML Form Filling + Email Sending to Broker
# Replaces TMS automation with form-based email submission

import json
import os
import time
import smtplib
from pathlib import Path
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# ============================================================================
# CONFIGURATION & PATHS
# ============================================================================

BASE_DIR = Path(__file__).resolve().parent
SHARED_DIR = BASE_DIR / "shared"
FORMS_DIR = BASE_DIR / "forms"
FORMS_SENT_DIR = FORMS_DIR / "sent"
FORMS_ARCHIVE_DIR = FORMS_DIR / "archive"

# Create directories
FORMS_SENT_DIR.mkdir(parents=True, exist_ok=True)
FORMS_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

USER_PROFILE_PATH = BASE_DIR / "user_profile.json"
FORM_TEMPLATE_PATH = BASE_DIR / "form_template.html"
SERIAL_NUMBER_FILE = SHARED_DIR / "last_serial.txt"
ORDERS_LOG_CSV = BASE_DIR / "orders_log.csv"

# ============================================================================
# NEPALI NUMBER CONVERSION
# ============================================================================

NEPALI_DIGITS = {
    '0': '०', '1': '१', '2': '२', '3': '३', '4': '४',
    '5': '५', '6': '६', '7': '७', '8': '८', '9': '९'
}

def to_nepali_number(num):
    """Convert English number to Nepali Devanagari digits"""
    return ''.join(NEPALI_DIGITS.get(c, c) for c in str(num))


# ============================================================================
# NEPALI DATE CONVERSION (Simple Approximation)
# ============================================================================

def english_to_nepali_date(date_str):
    """
    Convert English date to Nepali date (BS - Bikram Sambat)
    Input: "2025-01-05" format
    Output: "२०८१ पुष २१" format
    
    NOTE: This is a simplified conversion. For production, use nepali-datetime library
    BS year ≈ AD year + 56/57
    """
    try:
        from datetime import datetime
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        
        # Simple approximation: Add 56-57 years
        bs_year = dt.year + 57
        
        # Nepali month names (approximate mapping)
        nepali_months = [
            "बैशाख", "जेठ", "असार", "साउन", "भदौ", "असोज",
            "कार्तिक", "मंसिर", "पुष", "माघ", "फाल्गुन", "चैत"
        ]
        
        # Simple month approximation (this is NOT accurate, just for demo)
        # For production, use proper nepali-datetime library
        month_index = (dt.month + 8) % 12  # Rough approximation
        nepali_month = nepali_months[month_index]
        
        # Day approximation
        nepali_day = dt.day + 15  # Rough offset
        if nepali_day > 30:
            nepali_day = nepali_day - 30
            month_index = (month_index + 1) % 12
            nepali_month = nepali_months[month_index]
        
        # Format in Nepali
        bs_year_nepali = to_nepali_number(bs_year)
        nepali_day_str = to_nepali_number(nepali_day)
        
        return f"{bs_year_nepali} {nepali_month} {nepali_day_str}"
    
    except Exception as e:
        # Fallback
        return "२०८१ पुष २१"


def english_to_nepali_time(time_str):
    """Convert 24-hour time to Nepali numerals"""
    try:
        # time_str format: "14:35:22"
        return to_nepali_number(time_str)
    except:
        return "००:००:००"


# ============================================================================
# SERIAL NUMBER MANAGEMENT
# ============================================================================

def get_next_serial_number():
    """Get and increment serial number, starting from 888888"""
    try:
        if SERIAL_NUMBER_FILE.exists():
            with open(SERIAL_NUMBER_FILE, 'r') as f:
                last_serial = int(f.read().strip())
                next_serial = last_serial + 1
        else:
            next_serial = 888888
        
        # Write new serial number
        with open(SERIAL_NUMBER_FILE, 'w') as f:
            f.write(str(next_serial))
        
        return next_serial
    
    except Exception as e:
        # Fallback: use timestamp-based number
        return 888888 + int(time.time() % 100000)


# ============================================================================
# USER PROFILE LOADING
# ============================================================================

def load_user_profile():
    """Load user profile configuration"""
    try:
        with open(USER_PROFILE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise Exception(f"user_profile.json not found at {USER_PROFILE_PATH}")
    except json.JSONDecodeError as e:
        raise Exception(f"Invalid JSON in user_profile.json: {e}")


# ============================================================================
# PRICE CALCULATIONS
# ============================================================================

def calculate_price_ranges(base_price, config):
    """Calculate all three price ranges for the form"""
    try:
        base_price = float(base_price)
        
        # क) Fixed Price
        fixed_price = round(base_price, 2)
        
        # ख) Min/Max Range (±1%)
        min_max_percent = config.get('price_ranges', {}).get('min_max_range_percent', 0.01)
        min_price = round(base_price * (1 - min_max_percent), 2)
        max_price = round(base_price * (1 + min_max_percent), 2)
        
        # ग) Broker Discretion Range (±0.5%)
        broker_percent = config.get('price_ranges', {}).get('broker_discretion_percent', 0.005)
        broker_min = round(base_price * (1 - broker_percent), 2)
        broker_max = round(base_price * (1 + broker_percent), 2)
        
        return {
            'fixed': fixed_price,
            'min_max': f"{min_price} / {max_price}",
            'broker': f"{broker_min} / {broker_max}"
        }
    
    except Exception as e:
        return {
            'fixed': base_price,
            'min_max': f"{base_price} / {base_price}",
            'broker': f"{base_price} / {base_price}"
        }


# ============================================================================
# HTML FORM GENERATION
# ============================================================================

def generate_filled_form(signal, user_profile, serial_number):
    """
    Generate filled HTML form from template
    
    Args:
        signal: dict with keys: symbol, action, price, qty, timestamp
        user_profile: loaded user configuration
        serial_number: order serial number
    
    Returns:
        tuple: (html_content, form_filename)
    """
    try:
        # Load template
        with open(FORM_TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            template = f.read()
        
        # Extract signal data
        symbol = signal.get('symbol', 'UNKNOWN').upper()
        action = signal.get('action', 'BUY').upper()
        price = signal.get('price', 0)
        qty = signal.get('qty', user_profile.get('trading_defaults', {}).get('default_quantity', 10))
        timestamp = signal.get('timestamp', time.time())
        
        # Parse timestamp
        if isinstance(timestamp, (int, float)):
            dt = datetime.fromtimestamp(timestamp)
        else:
            dt = datetime.now()
        
        date_english = dt.strftime("%Y-%m-%d")
        time_english = dt.strftime("%H:%M:%S")
        
        # Convert to Nepali
        date_nepali = english_to_nepali_date(date_english)
        time_nepali = english_to_nepali_time(time_english)
        
        # Calculate price ranges
        prices = calculate_price_ranges(price, user_profile)
        
        # Get user info
        personal = user_profile.get('personal_info', {})
        trading = user_profile.get('trading_defaults', {})
        signature_info = user_profile.get('signature', {})
        
        # Build replacements dictionary
        replacements = {
            '{{SERIAL_NUMBER}}': to_nepali_number(serial_number),
            '{{DATE_NEPALI}}': date_nepali,
            '{{TIME_NEPALI}}': time_nepali,
            '{{DAYS_TO_EXECUTE}}': trading.get('days_to_execute', '७'),
            '{{COMPANY_NAME}}': symbol,
            '{{SECURITY_TYPE}}': trading.get('security_type', 'साधारण शेयर'),
            '{{QUANTITY}}': to_nepali_number(qty),
            '{{ACTION_PRICE}}': f"{action} @ रु.{price}",
            '{{SIGNATURE}}': signature_info.get('signature_text', ''),
            '{{FULL_NAME}}': personal.get('full_name', ''),
            '{{ADDRESS}}': personal.get('address', ''),
            '{{FATHER_NAME}}': personal.get('father_name', ''),
            '{{SPOUSE_GP_NAME}}': personal.get('spouse_or_grandfather_name', ''),
            '{{CITIZENSHIP_PAN}}': personal.get('citizenship_or_pan', ''),
            '{{DATE_OF_BIRTH}}': personal.get('date_of_birth', ''),
            '{{ISSUE_PLACE}}': personal.get('issue_place', ''),
            '{{MOBILE_NUMBER}}': personal.get('mobile_number', ''),
            '{{PHONE_NUMBER}}': personal.get('phone_number', ''),
            '{{CLIENT_CODE}}': personal.get('client_code', ''),
            '{{FIXED_PRICE}}': to_nepali_number(prices['fixed']),
            '{{MIN_MAX_PRICE}}': to_nepali_number(prices['min_max']),
            '{{BROKER_DISCRETION_PRICE}}': to_nepali_number(prices['broker'])
        }
        
        # Replace all placeholders
        filled_html = template
        for placeholder, value in replacements.items():
            filled_html = filled_html.replace(placeholder, str(value))
        
        # Generate filename
        timestamp_str = dt.strftime("%Y%m%d_%H%M%S")
        filename = f"form_{serial_number}_{symbol}_{action}_{timestamp_str}.html"
        
        return filled_html, filename
    
    except Exception as e:
        raise Exception(f"Failed to generate form: {e}")


# ============================================================================
# EMAIL SENDING
# ============================================================================

def send_email_with_form(html_content, filename, signal, user_profile, logger):
    """
    Send filled form via email to broker
    
    Args:
        html_content: filled HTML form content
        filename: form filename
        signal: original signal dict
        user_profile: user configuration
        logger: logging object
    
    Returns:
        bool: True if sent successfully
    """
    try:
        email_config = user_profile.get('email_config', {})
        
        # Email parameters
        broker_email = email_config.get('broker_email', 'avinaya@miyo66.com')
        sender_email = email_config.get('sender_email')
        sender_password = email_config.get('sender_password')
        smtp_server = email_config.get('smtp_server', 'smtp.gmail.com')
        smtp_port = email_config.get('smtp_port', 587)
        
        if not sender_email or not sender_password:
            logger.error("[EMAIL] Sender email or password not configured in user_profile.json")
            return False
        
        # Extract signal info
        symbol = signal.get('symbol', 'UNKNOWN')
        action = signal.get('action', 'BUY')
        price = signal.get('price', 0)
        qty = signal.get('qty', 10)
        serial_number = filename.split('_')[1]  # Extract from filename
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = broker_email
        msg['Subject'] = f"खरिद/बिक्री आदेश - दर्ता नं. {serial_number} - {symbol}"
        
        # Email body
        body = f"""महाशय,

कृपया संलग्न खरिद/बिक्री आदेश-पत्र अनुसार कारोबार गरिदिनुहोस्।

विवरण:
• दर्ता नं.: {serial_number}
• धितोपत्र: {symbol}
• कार्य: {action}
• मूल्य: रु. {price}
• संख्या: {qty}

धन्यवाद।

---
Automated Order System
NEPSE Trading Bot
"""
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Attach HTML form
        attachment = MIMEText(html_content, 'html', 'utf-8')
        attachment.add_header('Content-Disposition', f'attachment; filename="{filename}"')
        msg.attach(attachment)
        
        # Send email
        logger.info(f"[EMAIL] Connecting to {smtp_server}:{smtp_port}")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        
        logger.info(f"[EMAIL] Logging in as {sender_email}")
        server.login(sender_email, sender_password)
        
        logger.info(f"[EMAIL] Sending to {broker_email}")
        server.send_message(msg)
        server.quit()
        
        logger.info(f"[EMAIL] ✓ Successfully sent form {filename} to {broker_email}")
        return True
    
    except smtplib.SMTPAuthenticationError:
        logger.error("[EMAIL] Authentication failed. Check email/password in user_profile.json")
        logger.error("[EMAIL] For Gmail, use App Password: Google Account > Security > 2-Step > App passwords")
        return False
    
    except Exception as e:
        logger.error(f"[EMAIL] Failed to send email: {e}")
        return False


# ============================================================================
# CSV LOGGING
# ============================================================================

def log_order_to_csv(serial_number, signal, status, logger):
    """Log order details to CSV file"""
    try:
        import csv
        
        # Create CSV if it doesn't exist
        file_exists = ORDERS_LOG_CSV.exists()
        
        with open(ORDERS_LOG_CSV, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header if new file
            if not file_exists:
                writer.writerow([
                    'Serial', 'Timestamp', 'Date', 'Time', 'Symbol', 
                    'Action', 'Price', 'Quantity', 'Status'
                ])
            
            # Write order data
            now = datetime.now()
            writer.writerow([
                serial_number,
                now.strftime("%Y-%m-%d %H:%M:%S"),
                now.strftime("%Y-%m-%d"),
                now.strftime("%H:%M:%S"),
                signal.get('symbol', 'UNKNOWN'),
                signal.get('action', 'BUY'),
                signal.get('price', 0),
                signal.get('qty', 10),
                status
            ])
        
        logger.info(f"[LOG] Order logged to {ORDERS_LOG_CSV}")
    
    except Exception as e:
        logger.warning(f"[LOG] Failed to log order: {e}")


# ============================================================================
# MAIN EXECUTION FUNCTION
# ============================================================================

def execute_order(driver, signal: dict, logger, base_url=None):
    """
    Main order execution function (NEW VERSION)
    
    Instead of browser automation, this:
    1. Generates serial number
    2. Fills HTML form with signal + user data
    3. Sends form via email to broker
    4. Saves form locally
    5. Logs to CSV
    
    Args:
        driver: Not used anymore (kept for compatibility)
        signal: dict with symbol, action, price, qty, timestamp
        logger: logging object
        base_url: Not used (kept for compatibility)
    
    Returns:
        bool: True if form sent successfully
    """
    try:
        symbol = signal.get('symbol', 'UNKNOWN')
        action = signal.get('action', 'BUY')
        logger.info(f"[ORDER] Processing {action} order for {symbol}")
        
        # Step 1: Load user profile
        logger.info("[ORDER] Loading user profile...")
        user_profile = load_user_profile()
        
        # Step 2: Generate serial number
        serial_number = get_next_serial_number()
        logger.info(f"[ORDER] Generated serial number: {serial_number}")
        
        # Step 3: Generate filled form
        logger.info("[ORDER] Generating filled HTML form...")
        html_content, filename = generate_filled_form(signal, user_profile, serial_number)
        
        # Step 4: Save form locally
        form_path = FORMS_SENT_DIR / filename
        with open(form_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"[ORDER] Form saved to {form_path}")
        
        # Step 5: Send email
        logger.info("[ORDER] Sending form via email to broker...")
        email_sent = send_email_with_form(html_content, filename, signal, user_profile, logger)
        
        if not email_sent:
            logger.error("[ORDER] Failed to send email")
            log_order_to_csv(serial_number, signal, "EMAIL_FAILED", logger)
            return False
        
        # Step 6: Log to CSV
        log_order_to_csv(serial_number, signal, "SENT", logger)
        
        # Step 7: Archive form
        archive_path = FORMS_ARCHIVE_DIR / filename
        with open(archive_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"[ORDER] ✓ Order {serial_number} processed successfully")
        logger.info(f"[ORDER] {action} {symbol} @ {signal.get('price')} x {signal.get('qty')}")
        
        return True
    
    except Exception as e:
        logger.error(f"[ORDER] Order execution failed: {e}")
        logger.exception(e)
        return False