#!/bin/bash
cd documentacion
  mkdir -p doc
  mkdir -p doc/pyc
  cd ../src
  pydoc -w cliente
  pydoc -w proyectoDAO
  pydoc -w servidor
  pydoc -w usuario
  mv *.html ../documentacion/doc
  mv *.pyc ../documentacion/doc/pyc