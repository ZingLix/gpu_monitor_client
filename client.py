from flask import Flask, request
import subprocess
import xmltodict, pwd,json

app = Flask(__name__)
UID   = 1
EUID  = 2

def owner(pid):
    '''Return username of UID of process pid'''
    for ln in open('/proc/{}/status'.format(pid)):
        if ln.startswith('Uid:'):
            uid = int(ln.split()[UID])
            return pwd.getpwuid(uid).pw_name

def add_user(process):
    tmp = []
    for p in process:
        p["user"] = owner(p["pid"])
        tmp.append(p)
    return tmp

def simplify(gpu):
    tmp = {}
    for k in gpu.keys():
        if k in ["@id","product_name","uuid","fan_speed","fb_memory_usage","utilization","temperature","processes"]:
            tmp[k] = gpu[k]
    return tmp

def get_gpu_info():
    sp = subprocess.Popen(['nvidia-smi', '-q', '-x'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out_str = sp.communicate()
    out_str = out_str[0].decode("utf-8")
    o = xmltodict.parse(out_str)["nvidia_smi_log"]
    o = json.loads(json.dumps(o))
    gpu_list = []
    if not isinstance(o['gpu'], list):
        o['gpu'] = [o['gpu']]
    for gpu in o['gpu']:
        if gpu["processes"] is None:
            gpu["processes"] = {}
            gpu["processes"]["process_info"]=[]
        process = gpu["processes"]["process_info"]
        if not isinstance(process,list):
            process = [process]
        process = add_user(process)
        gpu["processes"]["process_info"] = process
        
        gpu = simplify(gpu)
        gpu_list.append(gpu)
    o["gpu"] = gpu_list
    return o

@app.route("/api/gpu_info/", methods=["GET"], strict_slashes=False)
def add_postprocess_file():
    return json.dumps(get_gpu_info())

app.run(host='0.0.0.0', port=12045, debug=False)
