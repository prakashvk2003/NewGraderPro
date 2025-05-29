import subprocess

def stop_ollama_model(model_name):    
    try:
        models_output = subprocess.check_output(["ollama", "ps"], text=True)
        models = []
        
        for line in models_output.strip().split("\n")[1:]:
            if line:
                parts = line.split()
                if len(parts) >= 1 and parts[0] == model_name:
                    kill_cmd = ["ollama", "stop", model_name]
                    subprocess.run(kill_cmd, check=True)
                    return True
        
        return False
    except subprocess.CalledProcessError:
        return False
