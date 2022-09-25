import time
from kubernetes import config
from kubernetes.client import Configuration
from kubernetes.client.api import core_v1_api
from kubernetes.client.rest import ApiException
from kubernetes.stream import stream
import json
import yaml
import os
from os.path import exists
import argparse
import fileinput
import regex as re


def patch_yaml(pod_file, context, destination, context_sub_path): 
    print("patching yaml...")

    # create file from template
    template = 'template.yaml'
    if exists(pod_file):
        os.remove(pod_file)
    with open(template,'r') as firstfile, open(pod_file,'w') as secondfile:
        for line in firstfile:
             secondfile.write(line)

    # replace tokens in file
    fields = {"[context]": context, "[destination]": destination, "[context-sub-path]": context_sub_path}
    flags=0
    with open(pod_file, "r+") as file:
        #read the file contents
        file_contents = file.read()
        for key, value in fields.items():
            text_pattern = re.compile(re.escape(key), flags)
            file_contents = text_pattern.sub(value, file_contents)
        file.seek(0)
        file.truncate()
        file.write(file_contents)
    print("patching yaml, done.")

def delete_pod(api_instance, name, namespace):
    print("Pod deleting...")
    api_response = api_instance.delete_namespaced_pod(name, namespace)
    print("Pod deleted...")    
    return api_response


def exec_commands(api_instance, context, destination, context_sub_path):
    pod_file = 'kaniko-docker-pod.yaml'
    namespace = 'kaniko'
    pod_name = 'kaniko-docker'
            
    resp = None
    try:
        resp = api_instance.read_namespaced_pod(name=pod_name,
                                                namespace=namespace)
    except ApiException as e:
        if e.status != 404:
            print("Unknown error: %s" % e)
            exit(1)
    if resp:        
        print(resp.status.phase)            
        if resp.status.phase == "Succeeded" or resp.status.phase == "Failed":
            resp = delete_pod(api_instance, pod_name, namespace)
            resp = None
        
    if not resp:
        print("Pod %s does not exist. Creating it..." % pod_name)

        patch_yaml(pod_file, context, destination, context_sub_path)
    
        with open(pod_file, 'r') as m:
            pod_manifest = yaml.safe_load(m)

        resp = api_instance.create_namespaced_pod(body=pod_manifest,
                                                  namespace=namespace)
        
        while True:
            resp = api_instance.read_namespaced_pod(name=pod_name,
                                                    namespace=namespace)
            print("working...")
            if resp.status.phase == 'Succeeded':
                break
            time.sleep(1)
            
        print("Image building is done.")
        print()

def main():
    parser = argparse.ArgumentParser(description='Constructor de imagenes docker que publica en docker hub')
    parser.version = '1.0'
    #parser.add_argument('-h', '--help', action='help')
    parser.add_argument('-c', '--context', type=str, help='contexto: repositorio git que contiene archivos para crear imagenes', required=True)
    parser.add_argument('-d', '--destination', type=str, help='destination: repositorio docker donde se subira la imagen', required=True)
    parser.add_argument('-p', '--context_sub_path', type=str, help='context sub path: subcarpeta del repositorio donde se encuentran los archivos para crear la imagen', required=True)
    args = parser.parse_args()

    config.load_kube_config()

    try:
        c = Configuration().get_default_copy()
    except AttributeError:
        c = Configuration()
        c.assert_hostname = False
    Configuration.set_default(c)
    core_v1 = core_v1_api.CoreV1Api()    

    exec_commands(core_v1, args.context, args.destination, args.context_sub_path)


if __name__ == '__main__':
    main()