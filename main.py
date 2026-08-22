
Search logs


Live tail



==> Downloading cache...
==> Cloning from https://github.com/lohhuixin1119-prog/adaptiveapi2
==> Checking out commit 49bf5d3780fc011bb2125bd10200390efc2be66d in branch main
==> Downloaded 25MB in 1s. Extraction took 0s.
==> Using Python version 3.14.3 (default)
==> Docs on specifying a Python version: https://render.com/docs/python-version
==> Installing Python version 3.14.3...
==> Using Poetry version 2.1.3 (default)
==> Docs on specifying a Poetry version: https://render.com/docs/poetry-version
==> Running build command 'pip install -r requirements.txt'...
Collecting fastapi (from -r requirements.txt (line 1))
  Using cached fastapi-0.141.1-py3-none-any.whl.metadata (27 kB)
Collecting uvicorn (from -r requirements.txt (line 2))
  Using cached uvicorn-0.52.4-py3-none-any.whl.metadata (6.6 kB)
Collecting starlette>=0.46.0 (from fastapi->-r requirements.txt (line 1))
  Using cached starlette-1.6.0-py3-none-any.whl.metadata (6.4 kB)
Collecting pydantic>=2.9.0 (from fastapi->-r requirements.txt (line 1))
  Using cached pydantic-2.13.4-py3-none-any.whl.metadata (109 kB)
Collecting typing-extensions>=4.8.0 (from fastapi->-r requirements.txt (line 1))
  Using cached typing_extensions-4.16.0-py3-none-any.whl.metadata (3.3 kB)
Collecting typing-inspection>=0.4.2 (from fastapi->-r requirements.txt (line 1))
  Using cached typing_inspection-0.4.4-py3-none-any.whl.metadata (2.6 kB)
Collecting annotated-doc>=0.0.2 (from fastapi->-r requirements.txt (line 1))
  Using cached annotated_doc-0.0.5-py3-none-any.whl.metadata (6.5 kB)
Collecting click>=7.0 (from uvicorn->-r requirements.txt (line 2))
  Using cached click-8.4.2-py3-none-any.whl.metadata (2.6 kB)
Collecting h11>=0.8 (from uvicorn->-r requirements.txt (line 2))
  Using cached h11-0.16.0-py3-none-any.whl.metadata (8.3 kB)
Collecting annotated-types>=0.6.0 (from pydantic>=2.9.0->fastapi->-r requirements.txt (line 1))
  Using cached annotated_types-0.8.0-py3-none-any.whl.metadata (15 kB)
Collecting pydantic-core==2.46.4 (from pydantic>=2.9.0->fastapi->-r requirements.txt (line 1))
  Using cached pydantic_core-2.46.4-cp314-cp314-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (6.6 kB)
Collecting anyio<5,>=3.6.2 (from starlette>=0.46.0->fastapi->-r requirements.txt (line 1))
  Using cached anyio-4.14.2-py3-none-any.whl.metadata (4.6 kB)
Collecting idna>=2.8 (from anyio<5,>=3.6.2->starlette>=0.46.0->fastapi->-r requirements.txt (line 1))
  Using cached idna-3.19-py3-none-any.whl.metadata (9.2 kB)
Using cached fastapi-0.141.1-py3-none-any.whl (131 kB)
Using cached uvicorn-0.52.4-py3-none-any.whl (79 kB)
Using cached annotated_doc-0.0.5-py3-none-any.whl (5.3 kB)
Using cached click-8.4.2-py3-none-any.whl (119 kB)
Using cached h11-0.16.0-py3-none-any.whl (37 kB)
Using cached pydantic-2.13.4-py3-none-any.whl (472 kB)
Using cached pydantic_core-2.46.4-cp314-cp314-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (2.1 MB)
Using cached annotated_types-0.8.0-py3-none-any.whl (13 kB)
Using cached starlette-1.6.0-py3-none-any.whl (75 kB)
Using cached anyio-4.14.2-py3-none-any.whl (125 kB)
Using cached idna-3.19-py3-none-any.whl (68 kB)
Using cached typing_extensions-4.16.0-py3-none-any.whl (45 kB)
Using cached typing_inspection-0.4.4-py3-none-any.whl (14 kB)
Installing collected packages: typing-extensions, idna, h11, click, annotated-types, annotated-doc, uvicorn, typing-inspection, pydantic-core, anyio, starlette, pydantic, fastapi
Successfully installed annotated-doc-0.0.5 annotated-types-0.8.0 anyio-4.14.2 click-8.4.2 fastapi-0.141.1 h11-0.16.0 idna-3.19 pydantic-2.13.4 pydantic-core-2.46.4 starlette-1.6.0 typing-extensions-4.16.0 typing-inspection-0.4.4 uvicorn-0.52.4
[notice] A new release of pip is available: 25.3 -> 26.2.1
[notice] To update, run: pip install --upgrade pip
==> Uploading build...
==> Uploaded in 1.6s. Compression took 1.8s
==> Build successful 🎉
==> Deploying...
==> Setting WEB_CONCURRENCY=1 by default, based on available CPUs in the instance
==> Running 'uvicorn main:app --host 0.0.0.0 --port $PORT'
INFO:     Started server process [58]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:10000 (Press CTRL+C to quit)
INFO:     127.0.0.1:40210 - "HEAD / HTTP/1.1" 404 Not Found
==> Your service is live 🎉
INFO:     34.82.226.193:0 - "GET / HTTP/1.1" 404 Not Found
==> 
==> ///////////////////////////////////////////////////////////
==> 
==> Available at your primary URL https://adaptiveapi2.onrender.com
==> 
==> ///////////////////////////////////////////////////////////
INFO:     54.164.156.151:0 - "POST /solve HTTP/1.1" 200 OK
