FROM node:11-stretch
RUN apt-get update && \
    apt-get install -qq -y build-essential python-pip curl
ADD . /myapp
WORKDIR /myapp
RUN pip install -r requirements.txt
RUN yarn install
RUN yarn run build
EXPOSE 5000
CMD FLASK_DEBUG=0 python main.py
