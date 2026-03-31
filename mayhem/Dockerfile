FROM fuzzers/atheris:2.0.7-python3.9

ADD . /src
WORKDIR /src
RUN pip3 install .

CMD ["/src/mayhem/fuzz_pack.py"]
