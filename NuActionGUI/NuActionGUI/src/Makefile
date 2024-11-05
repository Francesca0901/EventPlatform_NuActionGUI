grammars: ocl-grammar dtm-grammar stm-grammar ptm-grammar

ocl-grammar: ocl/parser/OclExpressionParser.py

ocl/parser/OclExpressionParser.py: OclExpression.g4
	antlr4 -visitor -listener -Dlanguage=Python3 OclExpression.g4 -o ocl/parser

dtm-grammar: dtm/parser/DataModelParser.py

dtm/parser/DataModelParser.py: DataModel.g4
	antlr4 -visitor -listener -Dlanguage=Python3 DataModel.g4 -o dtm/parser

stm-grammar: stm/parser/SecurityModelParser.py

stm/parser/SecurityModelParser.py: SecurityModel.g4
	antlr4 -visitor -listener -Dlanguage=Python3 SecurityModel.g4 -o stm/parser

ptm-grammar: ptm/parser/PrivacyModelParser.py

ptm/parser/PrivacyModelParser.py: PrivacyModel.g4
	antlr4 -visitor -listener -Dlanguage=Python3 PrivacyModel.g4 -o ptm/parser

clean:
	rm -f ocl/parser/OclExpression*
	rm -f dtm/parser/DataModel*
	rm -f stm/parser/SecurityModel*
	rm -f ptm/parser/PrivacyModel*

test: test-ocl test-dtm test-stm test-ptm

test-ocl: ocl/test
	python3 -m pytest -m safe -vv ocl/test/*.py

test-dtm: 
	python3 -m pytest -m safe -vv dtm/test/*.py

test-stm: 
	python3 -m pytest -m safe -vv stm/test/*.py

test-ptm: 
	python3 -m pytest -m safe -vv ptm/test/*.py
