# test_openai.py
try:
    import openai
    print("openai module is installed.")
except ModuleNotFoundError:
    print("openai module is not installed.")
