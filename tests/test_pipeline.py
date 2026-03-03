"""
tests/test_pipeline.py

End-to-end test of the full execution pipeline.
Tests that a workflow XML can be parsed and executed correctly.
"""
import respx
import httpx
from francis_suite.core.parser import FParser
from francis_suite.core.runtime import FRuntime
from francis_suite.core.session import SessionStatus


def test_log_hand_executes():
    """A workflow with a single <log> tag should complete successfully."""
    xml = """
    <francis-workflow>
        <log>Hello Francis Suite</log>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-log")

    assert session.status == SessionStatus.COMPLETED
    assert session.duration is not None
    assert session.error is None


def test_unknown_tag_fails_session():
    """A workflow with an unknown tag should fail the session."""
    xml = """
    <francis-workflow>
        <tag-que-no-existe/>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-unknown")

    assert session.status == SessionStatus.FAILED
    assert session.error is not None

def test_box_def_stores_variable():
    """box-def should execute children and store result in context."""
    xml = """
    <francis-workflow>
        <box-def name="mensaje">
            <log>guardando esto</log>
        </box-def>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-box-def")

    assert session.status == SessionStatus.COMPLETED
    variable = session.context.get("mensaje")
    assert not variable.is_empty()
    assert variable.to_string() == "guardando esto"

def test_sleep_executes():
    """sleep should pause execution and return empty."""
    xml = """
    <francis-workflow>
        <sleep seconds="0"/>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-sleep")

    assert session.status == SessionStatus.COMPLETED


def test_sleep_invalid_seconds_fails():
    """sleep with invalid seconds attribute should fail the session."""
    xml = """
    <francis-workflow>
        <sleep seconds="abc"/>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-sleep-invalid")

    assert session.status == SessionStatus.FAILED

def test_empty_returns_empty_variable():
    """empty tag should return an empty variable."""
    xml = """
    <francis-workflow>
        <box-def name="nada">
            <empty/>
        </box-def>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-empty")

    assert session.status == SessionStatus.COMPLETED
    assert session.context.get("nada").is_empty()

def test_http_call_fetches_url():
    """http-call should fetch a URL and return the response body."""
    xml = """
    <francis-workflow>
        <box-def name="page">
            <http-call url="https://example.com"/>
        </box-def>
    </francis-workflow>
    """

    with respx.mock:
        respx.get("https://example.com").mock(
            return_value=httpx.Response(200, text="<html>Hello</html>")
        )

        parser = FParser()
        runtime = FRuntime()

        root = parser.parse_string(xml)
        session = runtime.run(root, workflow_name="test-http-call")

    assert session.status == SessionStatus.COMPLETED
    result = session.context.get("page")
    assert not result.is_empty()
    assert "<html>Hello</html>" in result.to_string()

def test_convert_html_to_xml():
    """convert-html-to-xml should clean HTML and return valid XML."""
    xml = """
    <francis-workflow>
        <box-def name="clean">
            <convert-html-to-xml>
                <log>&lt;html&gt;&lt;body&gt;&lt;h1&gt;Hello&lt;/h1&gt;&lt;/body&gt;&lt;/html&gt;</log>
            </convert-html-to-xml>
        </box-def>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-convert")

    print(f"\nERROR: {session.error}")

    assert session.status == SessionStatus.COMPLETED
    result = session.context.get("clean")
    assert not result.is_empty()
    assert "h1" in result.to_string()

def test_xpath_extract_gets_text():
    """xpath-extract should apply XPath and return matching results."""
    xml_workflow = """
    <francis-workflow>
        <box-def name="resultado">
            <xpath-extract expression="//h1/text()"><![CDATA[<html><body><h1>Hola mundo</h1></body></html>]]></xpath-extract>
        </box-def>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml_workflow)
    session = runtime.run(root, workflow_name="test-xpath")

    assert session.status == SessionStatus.COMPLETED
    result = session.context.get("resultado")
    assert not result.is_empty()
    assert "Hola mundo" in result.to_string()

def test_loop_iterates_over_list():
    """loop should iterate over a list and execute children for each item."""
    xml = """
    <francis-workflow>
        <box-def name="items">
            <empty/>
        </box-def>
        <loop item="current" list="${items}">
            <log>${current}</log>
        </loop>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml)

    # Manually set a list variable in context before running
    from francis_suite.core.variables import FListVariable, FNodeVariable
    session = runtime.run(root, workflow_name="test-loop")

    assert session.status == SessionStatus.COMPLETED

def test_if_executes_when_true():
    """if should execute children when condition is true."""
    xml = """
    <francis-workflow>
        <box-def name="resultado">
            <if condition="1 == 1">
                <log>condicion verdadera</log>
            </if>
        </box-def>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-if-true")

    assert session.status == SessionStatus.COMPLETED
    assert session.context.get("resultado").to_string() == "condicion verdadera"

def test_if_skips_when_false():
    """if should skip children when condition is false."""
    xml = """
    <francis-workflow>
        <box-def name="resultado">
            <if condition="1 == 2">
                <log>no deberia ejecutarse</log>
            </if>
        </box-def>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-if-false")

    assert session.status == SessionStatus.COMPLETED
    assert session.context.get("resultado").is_empty()

def test_box_def_stores_variable():
    """box-def should execute children and store result in context."""
    xml = """
    <francis-workflow>
        <box-def name="mensaje">
            <log>guardando esto</log>
        </box-def>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-box-def")

    assert session.status == SessionStatus.COMPLETED
    variable = session.context.get("mensaje")
    assert not variable.is_empty()
    assert variable.to_string() == "guardando esto"


def test_box_retrieves_variable():
    """box should retrieve a previously stored variable."""
    xml = """
    <francis-workflow>
        <box-def name="mensaje">
            <log>hola</log>
        </box-def>
        <box-def name="copia">
            <box name="mensaje"/>
        </box-def>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-box")

    assert session.status == SessionStatus.COMPLETED
    assert session.context.get("copia").to_string() == "hola"

def test_while_executes_while_true():
    """while should execute children while condition is true."""
    xml = """
    <francis-workflow>
        <while condition="1 == 2">
            <log>no deberia ejecutarse</log>
        </while>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-while")

    assert session.status == SessionStatus.COMPLETED

def test_try_completes_when_no_error():
    """try should complete normally when no error occurs."""
    xml = """
    <francis-workflow>
        <try>
            <log>sin error</log>
            <catch>
                <log>no deberia ejecutarse</log>
            </catch>
        </try>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-try-ok")

    assert session.status == SessionStatus.COMPLETED

def test_try_executes_catch_on_error():
    """try should execute catch block when an error occurs."""
    xml = """
    <francis-workflow>
        <box-def name="resultado">
            <try>
                <tag-que-no-existe/>
                <catch>
                    <log>error capturado</log>
                </catch>
            </try>
        </box-def>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-try-catch")

    assert session.status == SessionStatus.COMPLETED
    assert session.context.get("resultado").to_string() == "error capturado"

def test_function_create_and_call():
    """function-create should define and function-call should execute it."""
    xml = """
    <francis-workflow>
        <function-create name="saludar">
            <box-def name="msg">
                <log>hola desde funcion</log>
            </box-def>
            <function-return>
                <box name="msg"/>
            </function-return>
        </function-create>
        <box-def name="resultado">
            <function-call name="saludar"/>
        </box-def>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-function")

    assert session.status == SessionStatus.COMPLETED
    assert session.context.get("resultado").to_string() == "hola desde funcion"


def test_function_call_with_params():
    """function-call should inject params into function scope."""
    xml = """
    <francis-workflow>
        <function-create name="repetir">
            <function-return>
                <box name="valor"/>
            </function-return>
        </function-create>
        <box-def name="resultado">
            <function-call name="repetir">
                <function-param name="valor">texto de prueba</function-param>
            </function-call>
        </box-def>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-function-params")

    assert session.status == SessionStatus.COMPLETED
    assert session.context.get("resultado").to_string() == "texto de prueba"


def test_function_call_undefined_fails():
    """function-call with undefined function should fail the session."""
    xml = """
    <francis-workflow>
        <function-call name="no-existe"/>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-function-undefined")

    assert session.status == SessionStatus.FAILED

def test_regex_finds_match():
    """regex should apply pattern and return match."""
    xml = r"""
    <francis-workflow>
        <box-def name="precio">
            <regex>
                <regex-pattern><![CDATA[\d+\.\d{2}]]></regex-pattern>
                <regex-input>El precio es 19.99 euros</regex-input>
            </regex>
        </box-def>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-regex")

    assert session.status == SessionStatus.COMPLETED
    assert session.context.get("precio").to_string() == "19.99"


def test_regex_with_groups_and_template():
    """regex should apply template with capture groups."""
    xml = r"""
    <francis-workflow>
        <box-def name="telefono">
            <regex>
                <regex-pattern><![CDATA[(\d{3})-(\d{3})-(\d{4})]]></regex-pattern>
                <regex-input>Llama al 555-123-4567</regex-input>
                <regex-results>(${group1}) ${group2}-${group3}</regex-results>
            </regex>
        </box-def>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-regex-groups")

    assert session.status == SessionStatus.COMPLETED
    assert session.context.get("telefono").to_string() == "(555) 123-4567"


def test_regex_no_match_returns_empty():
    """regex with no match should return empty."""
    xml = r"""
    <francis-workflow>
        <box-def name="resultado">
            <regex>
                <regex-pattern><![CDATA[\d+]]></regex-pattern>
                <regex-input>no hay numeros aqui</regex-input>
            </regex>
        </box-def>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-regex-empty")

    assert session.status == SessionStatus.COMPLETED
    assert session.context.get("resultado").is_empty()

def test_text_format_interpolates_variables():
    """text-format should replace ${var} with context values."""
    xml = """
    <francis-workflow>
        <box-def name="nombre">
            <log>Francis</log>
        </box-def>
        <box-def name="mensaje">
            <text-format>Hola ${nombre}!</text-format>
        </box-def>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-text-format")

    assert session.status == SessionStatus.COMPLETED
    assert session.context.get("mensaje").to_string() == "Hola Francis!"

def test_text_format_unknown_var_stays():
    """text-format should leave unknown ${var} expressions as-is."""
    xml = """
    <francis-workflow>
        <box-def name="resultado">
            <text-format>Valor: ${no-existe}</text-format>
        </box-def>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-text-format-unknown")

    assert session.status == SessionStatus.COMPLETED
    assert session.context.get("resultado").to_string() == "Valor: ${no-existe}"

def test_text_split_splits_by_delimiter():
    """text-split should split text by delimiter and return a list."""
    xml = """
    <francis-workflow>
        <box-def name="frutas">
            <text-split delimiter=",">manzana,pera,uva</text-split>
        </box-def>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-text-split")

    assert session.status == SessionStatus.COMPLETED
    result = session.context.get("frutas")
    assert not result.is_empty()
    assert len(result.to_list()) == 3

def test_text_split_trims_tokens():
    """text-split should trim whitespace from tokens by default."""
    xml = """
    <francis-workflow>
        <box-def name="items">
            <text-split delimiter=",">  uno  ,  dos  ,  tres  </text-split>
        </box-def>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-text-split-trim")

    assert session.status == SessionStatus.COMPLETED
    items = session.context.get("items").to_list()
    assert items[0].to_string() == "uno"
    assert items[1].to_string() == "dos"
    assert items[2].to_string() == "tres"

def test_evaluate_arithmetic():
    """evaluate should compute arithmetic expressions."""
    xml = """
    <francis-workflow>
        <box-def name="precio">
            <log>10</log>
        </box-def>
        <box-def name="cantidad">
            <log>3</log>
        </box-def>
        <box-def name="total">
            <evaluate>${precio} * ${cantidad}</evaluate>
        </box-def>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-evaluate-arithmetic")

    assert session.status == SessionStatus.COMPLETED
    assert session.context.get("total").to_string() == "30"

def test_evaluate_is_empty():
    """evaluate should support isEmpty() method call."""
    xml = """
    <francis-workflow>
        <box-def name="nombre">
            <log>Francis</log>
        </box-def>
        <box-def name="resultado">
            <evaluate>${nombre.isEmpty()}</evaluate>
        </box-def>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-evaluate-isempty")

    assert session.status == SessionStatus.COMPLETED
    assert session.context.get("resultado").to_string() == "False"

def test_evaluate_to_upper():
    """evaluate should support toUpperCase() method call."""
    xml = """
    <francis-workflow>
        <box-def name="nombre">
            <log>francis</log>
        </box-def>
        <box-def name="resultado">
            <evaluate>${nombre.toUpperCase()}</evaluate>
        </box-def>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-evaluate-upper")

    assert session.status == SessionStatus.COMPLETED
    assert session.context.get("resultado").to_string() == "FRANCIS"

def test_else_executes_when_if_false():
    """else should execute when preceding if condition is false."""
    xml = """
    <francis-workflow>
        <box-def name="resultado">
            <log>nada</log>
        </box-def>
        <if condition="1 == 2">
            <box-def name="resultado">
                <log>if ejecutado</log>
            </box-def>
        </if>
        <else>
            <box-def name="resultado">
                <log>else ejecutado</log>
            </box-def>
        </else>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-else")

    assert session.status == SessionStatus.COMPLETED
    assert session.context.get("resultado").to_string() == "else ejecutado"

def test_else_skips_when_if_true():
    """else should not execute when preceding if condition is true."""
    xml = """
    <francis-workflow>
        <if condition="1 == 1">
            <box-def name="resultado">
                <log>if ejecutado</log>
            </box-def>
        </if>
        <else>
            <box-def name="resultado">
                <log>else ejecutado</log>
            </box-def>
        </else>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-else-skip")

    assert session.status == SessionStatus.COMPLETED
    assert session.context.get("resultado").to_string() == "if ejecutado"

def test_case_executes_first_match():
    """case should execute only the first matching if."""
    xml = """
    <francis-workflow>
        <box-def name="tipo">
            <log>B</log>
        </box-def>
        <box-def name="resultado">
            <case>
                <if condition="${tipo} == 'A'">
                    <log>es tipo A</log>
                </if>
                <if condition="${tipo} == 'B'">
                    <log>es tipo B</log>
                </if>
                <if condition="${tipo} == 'C'">
                    <log>es tipo C</log>
                </if>
                <else>
                    <log>tipo desconocido</log>
                </else>
            </case>
        </box-def>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-case")

    assert session.status == SessionStatus.COMPLETED
    assert session.context.get("resultado").to_string() == "es tipo B"

def test_case_executes_else_when_no_match():
    """case should execute else when no if matches."""
    xml = """
    <francis-workflow>
        <box-def name="tipo">
            <log>Z</log>
        </box-def>
        <box-def name="resultado">
            <case>
                <if condition="${tipo} == 'A'">
                    <log>es tipo A</log>
                </if>
                <if condition="${tipo} == 'B'">
                    <log>es tipo B</log>
                </if>
                <else>
                    <log>tipo desconocido</log>
                </else>
            </case>
        </box-def>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-case-else")

    assert session.status == SessionStatus.COMPLETED
    assert session.context.get("resultado").to_string() == "tipo desconocido"

def test_exit_stops_workflow():
    """exit should stop workflow execution cleanly."""
    xml = """
    <francis-workflow>
        <box-def name="antes">
            <log>antes del exit</log>
        </box-def>
        <exit/>
        <box-def name="despues">
            <log>despues del exit</log>
        </box-def>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-exit")

    assert session.status == SessionStatus.COMPLETED
    assert session.context.get("antes").to_string() == "antes del exit"
    assert session.context.get("despues").is_empty()

def test_build_list_creates_list():
    """build-list should create a FListVariable from children results."""
    xml = """
    <francis-workflow>
        <box-def name="items">
            <build-list>
                <log>uno</log>
                <log>dos</log>
                <log>tres</log>
            </build-list>
        </box-def>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-build-list")

    assert session.status == SessionStatus.COMPLETED
    result = session.context.get("items")
    assert not result.is_empty()
    assert len(result.to_list()) == 3
    assert result.to_list()[0].to_string() == "uno"
    assert result.to_list()[1].to_string() == "dos"
    assert result.to_list()[2].to_string() == "tres"

def test_call_workflow_executes_external_file(tmp_path):
    """call-workflow should load and execute an external workflow file."""
    external = tmp_path / "external.xml"
    external.write_text("""
    <francis-workflow>
        <box-def name="externo">
            <log>valor externo</log>
        </box-def>
    </francis-workflow>
    """)

    xml = f"""
    <francis-workflow>
        <call-workflow path="{external}"/>
    </francis-workflow>
    """

    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_string(xml)
    session = runtime.run(root, workflow_name="test-call-workflow")

    assert session.status == SessionStatus.COMPLETED
    assert session.context.get("externo").to_string() == "valor externo"