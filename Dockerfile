FROM python:2-stretch

RUN mkdir /get5
WORKDIR /get5
ADD . .
RUN pip install -r requirements.txt
RUN chmod a+rx entry.sh

CMD ./entry.sh
