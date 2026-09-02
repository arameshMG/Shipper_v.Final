import traceback
import json


def debug_log(label, **context):
    """
    Universal debug logger. Call this anywhere you want visibility,
    or inside an except block to capture a full error report.

    Usage (normal checkpoint):
        debug_log("Before Graph call", user_email=user_email, url=url)

    Usage (inside an error):
        except Exception as e:
            debug_log("Graph lookup failed", error=e, user_email=user_email, url=url)
    """
    print("\n" + "=" * 60)
    print(f"DEBUG LOG: {label}")
    print("=" * 60)

    for key, value in context.items():
        if key == "error" and isinstance(value, Exception):
            print(f"ERROR TYPE: {type(value).__name__}")
            print(f"ERROR MESSAGE: {str(value)}")
            print("TRACEBACK:")
            print(traceback.format_exc())
        else:
            try:
                print(f"{key.upper()}: {json.dumps(value, indent=2, default=str)}")
            except Exception:
                print(f"{key.upper()}: {repr(value)}")

    print("=" * 60 + "\n")
