FROM amazon/aws-lambda-python:3.10
RUN /var/lang/bin/python3.10 -m pip install --upgrade pip
RUN yum install git -y
ARG ACCESS_KEY
ARG SECRET_KEY
ENV ACCESS_KEY=${ACCESS_KEY}
ENV SECRET_KEY=${SECRET_KEY}
RUN yum install -y gcc gcc-c++ cmake make tar
RUN curl -L -o /tmp/ffmpeg-release-amd64-static.tar.xz https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz && \
    yum install -y xz && \
    tar -xJf /tmp/ffmpeg-release-amd64-static.tar.xz --strip-components=1 -C /usr/local/bin && \
    rm /tmp/ffmpeg-release-amd64-static.tar.xz && \
    chmod +x /usr/local/bin/ffmpeg
RUN curl -sL https://rpm.nodesource.com/setup_16.x | bash - && \
    yum install -y nodejs
RUN npm install -g @mermaid-js/mermaid-cli
RUN /var/lang/bin/python3.10 -m pip install llama-cpp-python
RUN /var/lang/bin/python3.10 -m pip install torch==2.1.0 --index-url https://download.pytorch.org/whl/cpu
RUN git clone https://github.com/Han-16/clerker-ai.git
RUN /var/lang/bin/python3.10 -m pip install -r clerker-ai/requirements.txt
COPY Chunking /var/task/ && \
    Diagrams /var/task/ && \
    Keywords /var/task/ && \
    STT /var/task/
COPY lambda_function.py /var/task/
CMD ["lambda_function.handler"]