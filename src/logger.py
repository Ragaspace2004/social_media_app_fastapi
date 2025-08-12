import logging
import json
import os
from datetime import datetime
import pytz

class JSONFormatter(logging.Formatter):
    def format(self,record):
        # Get IST timezone
        ist = pytz.timezone('Asia/Kolkata')
        ist_time = datetime.now(ist)
        
        log_entry = {
          "timestamp": ist_time.strftime('%Y-%m-%d %H:%M:%S IST'),
          "level":record.levelname,
          "logger":record.name,
          "message":record.getMessage()
        }
        
        if hasattr(record,'event_type'):
           log_entry['event_type']=record.event_type
        if hasattr(record,'username'):
           log_entry['username']=record.username
        if hasattr(record,'ip_address'):
           log_entry['ip_address']=record.ip_address
        if hasattr(record,'endpoint'):
           log_entry['endpoint']=record.endpoint
        if hasattr(record,'reason'):
           log_entry['reason']=record.reason
        if hasattr(record,'user_agent'):
           log_entry['user_agent']=record.user_agent
        return json.dumps(log_entry)
      
# Create logs directory if it doesn't exist
def setup_logger():
    # Get project root directory (parent of src directory)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    logs_dir = os.path.join(project_root, 'logs')
    
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
        
    console_formatter = logging.Formatter(
      '%(asctime)s IST - %(name)s - %(levelname)s - %(message)s'
    )
    # Set IST timezone for console output
    console_formatter.converter = lambda *args: datetime.now(pytz.timezone('Asia/Kolkata')).timetuple()
    json_formatter=JSONFormatter()
    log_file_path = os.path.join(logs_dir, 'app.json')
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(json_formatter)
    
    console_handler=logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    root_logger=logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

# Initialize logger when module is imported
setup_logger()
security_logger=logging.getLogger("SECURITY")

def log_auth_success(username:str,ip:str,user_agent:str=None):
    extra = {
      'event_type':'auth_success',
    }
    if user_agent:
       extra['user_agent']=user_agent
    security_logger.info(
      f'AUTH SUCCESS - User:{username}, IP:{ip}',extra=extra
    )
    
def log_auth_failed(username:str,ip:str,reason:str="invalid credentials",user_agent:str=None):
    extra = {
      'event_type':'auth_failed'
    }
    if user_agent:
       extra['user_agent']=user_agent
    security_logger.info(
      f'AUTH FAILED - User:{username}, IP:{ip}, Reason:{reason}',extra=extra
    )

def log_rate_limit(ip:str,endpoint:str,user_agent:str=None):
    extra={
      'event_type':'rate_limit_exceeded'
    }
    if user_agent:
       extra['user_agent']=user_agent
    security_logger.info(
      f'RATE LIMIT EXCEEDED - IP:{ip}, Endpoint:{endpoint}',extra=extra
    )

def log_unauthorized_access(ip:str, endpoint:str,reason:str="invalid token",user_agent:str=None):
    extra={
      'event_type':'unauthorized_access'
    }
    if user_agent:
       extra['user_agent']=user_agent
    security_logger.info(
      f'UNAUTHORIZED ACCESS - IP:{ip}, Endpoint:{endpoint}, Reason:{reason}',extra=extra
    )

def log_user_action(username:str,action:str,details:str=None,user_agent:str=None):
    extra={
      'event_type':'user_action'
    }
    if details:
       extra['details']=details
    security_logger.info(
      f'USER ACTION - User:{username}, Action:{action}, Details:{details}',extra=extra
    )

def log_error(message: str, error: str = "", endpoint: str = None, ip: str = None):
    extra = {
        'event_type': 'error'
        }
    if endpoint:
        extra['endpoint'] = endpoint
    if ip:
        extra['ip_address'] = ip
    
    security_logger.error(
        f"ERROR - {message} - {error}",
        extra=extra
    )
    
def log_info(message: str, details: dict = None):
    extra = {
        'event_type': 'info'
    }
    if details:
        extra.update(details)
    
    security_logger.info(
        f"INFO - {message}",
        extra=extra
    )
    
def get_client_ip(request):
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

def get_user_agent(request):
    return request.headers.get("user-agent", "unknown")

def log_security_event(event_type: str, details: dict = None, ip: str = None):
    extra = {
        'event_type': event_type
    }
    if details:
        extra.update(details)
    if ip:
        extra['ip_address'] = ip
    
    # Format message based on event type
    if event_type == "login_success":
        message = f"LOGIN SUCCESS - User: {details.get('username', 'unknown')}"
    elif event_type == "login_failed":
        message = f"LOGIN FAILED - User: {details.get('username', 'unknown')}, Reason: {details.get('reason', 'unknown')}"
    elif event_type == "account_locked_attempt":
        message = f"ACCOUNT LOCKED ATTEMPT - User: {details.get('username', 'unknown')}"
    elif event_type == "expired_token":
        message = f"EXPIRED TOKEN - User: {details.get('username', 'unknown')}"
    elif event_type == "invalid_token":
        message = f"INVALID TOKEN - Reason: {details.get('reason', 'unknown')}"
    elif event_type == "user_not_found":
        message = f"USER NOT FOUND - User: {details.get('username', 'unknown')}"
    else:
        message = f"SECURITY EVENT - Type: {event_type}"
    
    security_logger.info(message, extra=extra)