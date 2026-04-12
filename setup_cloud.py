import os

files_to_create = [
    "server/api.py",
    "server/voice_ws.py",
    "server/auth.py",
    "server/session_manager.py",
    "core/license/usage_limit_engine.py",
    "core/license/feature_gate.py",
    "core/license/license_client.py",
    "core/referral/referral_engine.py",
    "core/security/hardrock_security.py",
    "core/perception/perception_buffer.py",
    "core/perception/event_detector.py",
    "core/perception/perception_stream.py",
    "lite/client/login.html",
    "lite/client/signup.html",
    "lite/client/dashboard.html"
]

created_files = []

for file_path in files_to_create:
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            pass
        created_files.append(file_path)

env_path = ".env"
env_additions = """
CLOUD_MODE=true

DATABASE_URL=
REDIS_URL=

FIREBASE_PROJECT_ID=
FIREBASE_API_KEY=
FIREBASE_PRIVATE_KEY=

STT_API_KEY=
TTS_API_KEY=

SENTRY_DSN=
LOGTAIL_SOURCE_TOKEN=

LICENSE_SERVER_URL=

RSA_PUBLIC_KEY=
RSA_PRIVATE_KEY=
"""

if os.path.exists(env_path):
    with open(env_path, "r") as f:
        content = f.read()
else:
    content = ""

# Instead of checking one by one, we append if CLOUD_MODE doesn't exist
if "CLOUD_MODE=" not in content:
    with open(env_path, "a") as f:
        # Prepend a newline just in case the file doesn't end with one
        if content and not content.endswith("\\n"):
            f.write("\\n")
        f.write(env_additions)
    print("Updated: .env")

print("Created the following files:")
for f in created_files:
    print(f)
