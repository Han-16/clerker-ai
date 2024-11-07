import os
import json
import boto3
from STT.ClovaText import make_stt_txt
from Chunking.EmbeddingChunking import make_chunk
from Keywords.BllossomKeyword_to_md import generate_summary_jsons, generate_report_from_json
from Diagrams.DiagramGeneration import diagram_gen

# S3 클라이언트 초기화
ACCESS_KEY = os.environ.get("ACCESS_KEY")
SECRET_KEY = os.environ.get("SECRET_KEY")
bucket_name = "clerker-ai.bucket"

s3 = boto3.client(
    's3',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY
    )

def download_from_s3(s3_path, local_path):
    s3.download_file(bucket_name, s3_path, local_path)

def upload_to_s3(local_path, s3_path):
    s3.upload_file(local_path, bucket_name, s3_path)

def download_folder_from_s3(s3_folder, local_dir):
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket_name, Prefix=s3_folder):
        if 'Contents' in page:
            for obj in page['Contents']:
                key = obj['Key']
                if key.endswith('/'):
                    # 디렉토리는 스킵
                    continue
                # 로컬 파일 경로 생성
                relative_path = key[len(s3_folder):].lstrip('/')
                local_file_path = os.path.join(local_dir, relative_path)
                # 필요한 디렉토리 생성
                local_file_dir = os.path.dirname(local_file_path)
                os.makedirs(local_file_dir, exist_ok=True)
                # 파일 다운로드
                s3.download_file(bucket_name, key, local_file_path)


def lambda_handler(event, context):
    os.makedirs('/tmp/STT', exist_ok=True)
    os.makedirs('/tmp/STT/stt_audio', exist_ok=True)
    os.makedirs('/tmp/STT/stt_text/KeywordBoosting', exist_ok=True)
    os.makedirs('/tmp/Chunking', exist_ok=True)
    os.makedirs('/tmp/Keywords', exist_ok=True)
    os.makedirs('/tmp/Diagrams', exist_ok=True)
    os.makedirs('/tmp/Diagrams/mermaid', exist_ok=True)
    os.makedirs('/tmp/models', exist_ok=True)
    os.makedirs('/tmp/models/models--MLP-KTLim--llama-3-Korean-Bllossom-8B-gguf-Q4_K_M', exist_ok=True)
    os.makedirs('/tmp/Keywords/NanumFontSetup_TTF_SQUARE_ROUND', exist_ok=True)
    print("current directory: ", os.getcwd())
    # Lambda 핸들러 함수

    # 입력 이벤트에서 도메인과 mp3 파일 URL을 가져옵니다.
    input_domain = event.get('domain', 'IT')
    mp3_file_url = event.get('mp3FileUrl', "input_audio.mp3")
    print("mp3_file_url: ", mp3_file_url)

    # 파일 경로 설정
    input_audio_file = '/tmp/STT/stt_audio/input_audio.mp3'
    output_txt_file = '/tmp/STT/stt_text/stt_text.txt'
    output_chunk_dict = '/tmp/Chunking/chunking_text.json'
    output_summary_json = '/tmp/Keywords/summary.json'
    diagram_summary_json = '/tmp/Diagrams/diagram_summary.json'
    output_report_md = '/tmp/Keywords/report.md'
    s3_font_path = 'Keywords/NanumFontSetup_TTF_SQUARE_ROUND/NanumSquareRoundB.ttf'
    font_path = f'/tmp/{s3_font_path}'

    # 1. S3에서 mp3 파일 다운로드
    # mp3_file_url은 S3의 키로 간주합니다.
    download_from_s3(mp3_file_url, input_audio_file)

    # 2. Keyword Boosting JSON 파일 다운로드
    keyword_boosting_domain = f'STT/stt_text/KeywordBoosting/{input_domain}_KeywordBoosting.json'
    keyword_boosting_agenda = 'STT/stt_text/KeywordBoosting/Agenda_middle.json'
    local_keyword_boosting_domain = f'/tmp/STT/stt_text/KeywordBoosting/{input_domain}_KeywordBoosting.json'
    local_keyword_boosting_agenda = '/tmp/STT/stt_text/KeywordBoosting/Agenda_middle.json'

    download_from_s3(keyword_boosting_domain, local_keyword_boosting_domain)
    download_from_s3(keyword_boosting_agenda, local_keyword_boosting_agenda)

    # 3. 모델 파일 다운로드
    # local_model_dir = '/tmp/models'
    # os.makedirs(local_model_dir, exist_ok=True)
    # # 모델 파일 목록을 정의합니다.
    # model_folders = [
    #     'models--jhgan--ko-sroberta-sts/snapshots/3efa8e54a06798b00bd1abb9c22b2dd530e22b24/',
    #     'models--MLP-KTLim--llama-3-Korean-Bllossom-8B-gguf-Q4_K_M/snapshots/4e602ad115392e7298674e092d6f8b45138f1db7/',
    #     'models--MLP-KTLim--llama-3-Korean-Bllossom-8B-gguf-Q4_K_M/llama-3-Korean-Bllossom-8B-Q4_K_M.gguf',
    # ]
    # model_files = []
    # for model_file in model_files:
    #     print(f"Downloading model file: {model_file}")
    #     s3_model_path = f'models/{model_file}'
    #     local_model_path = os.path.join(local_model_dir, os.path.basename(model_file))
    #     print(f"local_model_path: {local_model_path}")
    #     download_from_s3(s3_model_path, local_model_path)
    
    #  3. 모델 폴더 다운로드
    local_model_dir = '/tmp/models'
    os.makedirs(local_model_dir, exist_ok=True)
    # 모델 폴더 목록을 정의합니다.
    model_folders = [
        'models--jhgan--ko-sroberta-sts/snapshots/3efa8e54a06798b00bd1abb9c22b2dd530e22b24/',
        'models--MLP-KTLim--llama-3-Korean-Bllossom-8B-gguf-Q4_K_M/snapshots/4e602ad115392e7298674e092d6f8b45138f1db7/',
    ]
    for model_folder in model_folders:
        s3_model_folder = f'models/{model_folder}'
        local_model_folder = os.path.join(local_model_dir, model_folder)
        print(f"Downloading model folder from S3: {s3_model_folder}")
        download_folder_from_s3(s3_model_folder, local_model_folder)

    s3_bllossom_path = "models/models--MLP-KTLim--llama-3-Korean-Bllossom-8B-gguf-Q4_K_M/llama-3-Korean-Bllossom-8B-Q4_K_M.gguf"
    local_bllossom_path = os.path.join("/tmp", s3_bllossom_path)
    print("local_bllossom_path: ", local_bllossom_path)

    download_from_s3(s3_bllossom_path, local_bllossom_path)
    download_from_s3(s3_font_path, font_path)
    # 4. STT 파일 생성
    make_stt_txt(
        input_domain,
        input_audio_file,
        output_txt_file,
        local_keyword_boosting_domain,
        local_keyword_boosting_agenda
    )
    print(f"STT 파일 생성 완료 : {output_txt_file}")

    # 5. Chunk 생성
    make_chunk(output_txt_file, output_chunk_dict)
    print(f"Chunk Dict 파일 생성 완료 : {output_chunk_dict}")

    # 6. 요약 및 다이어그램용 JSON 파일 생성
    generate_summary_jsons(
        output_chunk_dict,
        diagram_summary_json,
        output_summary_json,
        model_id=os.path.join(local_model_dir, 'models--MLP-KTLim--llama-3-Korean-Bllossom-8B-gguf-Q4_K_M'),
        model_path=os.path.join(local_model_dir, 'models--MLP-KTLim--llama-3-Korean-Bllossom-8B-gguf-Q4_K_M/llama-3-Korean-Bllossom-8B-Q4_K_M.gguf')
    )
    print(f"다이어그램 및 보고서용 JSON 파일 생성 완료 : {output_summary_json}")

    # 7. 다이어그램 생성
    diagram_gen(diagram_summary_json)
    print("다이어그램 생성 완료")

    # 8. 보고서 생성
    generate_report_from_json(output_summary_json, output_report_md)
    print(f"Report 파일 생성 완료 : {output_report_md}")

    # 9. 결과 파일을 S3에 업로드
    upload_to_s3(output_txt_file, 'STT/stt_text/stt_text.txt')
    upload_to_s3(output_chunk_dict, 'Chunking/chunking_text.json')
    upload_to_s3(output_summary_json, 'Keywords/summary.json')
    upload_to_s3(output_report_md, 'Keywords/report.md')
    # 다이어그램 이미지들이 저장된 경로를 지정하여 업로드
    diagram_images_dir = '/tmp/Diagrams/mermaid'
    for root, dirs, files in os.walk(diagram_images_dir):
        for file in files:
            local_file_path = os.path.join(root, file)
            s3_file_path = f'Diagrams/mermaid/{file}'
            upload_to_s3(local_file_path, s3_file_path)

    # 10. 응답 생성
    response = {
        "report": f"https://{bucket_name}.s3.amazonaws.com/Keywords/report.md",
        "stt": f"https://{bucket_name}.s3.amazonaws.com/STT/stt_text/stt_text.txt",
        "diagram_image": f"https://{bucket_name}.s3.amazonaws.com/Diagrams/mermaid.zip"
    }

    return {
        "statusCode": 200,
        "body": json.dumps(response)
    }
