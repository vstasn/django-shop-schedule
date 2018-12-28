FROM python:3.6
ENV PYTHONUNBUFFERED 1
RUN mkdir /django-shop-schedule
WORKDIR /django-shop-schedule
COPY requirements.txt /django-shop-schedule/
RUN pip install -r requirements.txt
COPY . /django-shop-schedule/
