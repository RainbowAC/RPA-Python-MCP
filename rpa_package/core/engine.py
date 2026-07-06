"""
RPA for Python - Tagui Engine Core
"""

import os
import sys
import time
import platform
import subprocess
import zipfile
from typing import Optional

from .config import __version__, Config, TAGUI_LOCAL_JS
from .exceptions import TagUIProcessError
from .io_helpers import IOHelper

# ---------------------------------------------------------------------------
# 外部依赖下载地址（可根据企业环境修改）
# ---------------------------------------------------------------------------
_TAGUI_RELEASE_BASE_URL = 'https://github.com/tebelorg/Tump/releases/download/v1.0.0'
_TAGUI_RAW_BASE_URL = 'https://raw.githubusercontent.com/tebelorg/Tump/master'
_TAGUI_RPA_RAW_URL = 'https://raw.githubusercontent.com/tebelorg/RPA-Python/master/tagui.py'
_TELEGRAM_BOT_ENDPOINT = 'https://tebel.org/rpapybot'
_BIN_SERVER_URL = 'https://tebel.org/bin/'


class TaguiEngine:
    """Main engine for RPA for Python - manages TagUI process and communication."""

    def __init__(self) -> None:
        self._config = Config()
        self._io = IOHelper(delay=self._config.delay)
        self._process: Optional[subprocess.Popen] = None
        self._started: bool = False
        self._visual: bool = False
        self._chrome: bool = False
        self._id: int = 0
        self._init_directory: str = ''
        self._download_directory: str = ''

    @property
    def config(self) -> Config:
        return self._config

    @property
    def started(self) -> bool:
        return self._started

    @property
    def visual(self) -> bool:
        return self._visual

    @property
    def chrome(self) -> bool:
        return self._chrome

    @property
    def init_directory(self) -> str:
        return self._init_directory

    @property
    def download_directory(self) -> str:
        return self._download_directory

    def _read_line(self) -> str:
        if self._process is None:
            raise TagUIProcessError('No active TagUI process')
        return self._process.stdout.readline().decode('utf-8')

    def _write_line(self, text: str = '') -> None:
        if self._process is None:
            raise TagUIProcessError('No active TagUI process')
        self._process.stdin.write(text.encode('utf-8'))
        self._process.stdin.flush()

    def _escape_single_quote(self, text: str) -> str:
        return text.replace("'", '[BACKSLASH_QUOTE]')

    def _escape_xpath_quote(self, text: str) -> str:
        return text.replace("'", '"')

    def _output(self) -> str:
        output_file = 'rpa_python.txt'
        fallback = os.path.join(self._init_directory, 'rpa_python.txt') if self._init_directory else None
        return self._io.wait_for_output_file(output_file, fallback)

    def _ready(self) -> bool:
        if not self._started:
            return False
        if self._process is None or self._process.poll() is not None:
            self._visual = False
            self._chrome = False
            self._started = False
            return False
        tagui_out = self._read_line()
        if self._config.debug:
            sys.stdout.write(tagui_out)
            sys.stdout.flush()
        if tagui_out.strip().startswith('[RPA][') and tagui_out.strip().endswith('] - listening for inputs'):
            return True
        return False

    def _write_entry_flow(self, visual_automation: bool) -> None:
        if visual_automation:
            flow_text = (
                '// VISUAL ENTRY FLOW FOR RPA FOR PYTHON ~ TEBEL.ORG\r\n'
                '// mouse_xy() - dummy trigger for SikuliX integration\r\n\r\nlive'
            )
        else:
            flow_text = '// NORMAL ENTRY FLOW FOR RPA FOR PYTHON ~ TEBEL.ORG\r\n\r\nlive'
        self._io.dump_file(flow_text, 'rpa_python')

    def _write_local_js(self) -> None:
        self._io.dump_file(TAGUI_LOCAL_JS, 'tagui_local.js')

    def _cleanup_files(self) -> None:
        for f in ['rpa_python', 'rpa_python.js', 'rpa_python.raw', 'tagui_local.js']:
            self._io.safe_remove(f)
            if self._init_directory:
                self._io.safe_remove(os.path.join(self._init_directory, f))

    def _handle_error(self, message: str) -> bool:
        if self._config.error_mode:
            raise TagUIProcessError(message)
        print(message)
        return False

    def _download_file(self, url: str, filename: str) -> bool:
        if not url:
            return self._handle_error('[RPA][ERROR] - download URL missing')
        if not filename:
            tokens = url.split('/')
            filename = tokens[-1]
        if TaguiEngine.download(url, filename):
            return True
        return self._handle_error(f'[RPA][ERROR] - failed downloading to {filename}')

    @staticmethod
    def _unzip_file(file_path: str, extract_dir: Optional[str] = None) -> None:
        with zipfile.ZipFile(file_path, 'r') as zf:
            if extract_dir:
                zf.extractall(extract_dir)
            else:
                zf.extractall()

    def setup(self) -> bool:
        """Setup TagUI to user home folder on Linux / macOS / Windows."""
        home_directory = self._config.tagui_location
        print('[RPA][INFO] - setting up TagUI for use in your Python environment')

        if platform.system() == 'Darwin':
            for ver in ['3.9', '3.8', '3.7', '3.6']:
                cmd = f'/Applications/Python {ver}/Install Certificates.command'
                if os.system(f'{cmd} > /dev/null 2>&1') == 0:
                    break

        os_map = {'Linux': 'TagUI_Linux.zip', 'Darwin': 'TagUI_macOS.zip', 'Windows': 'TagUI_Windows.zip'}
        tagui_zip_file = os_map.get(platform.system())
        if tagui_zip_file is None:
            return self._handle_error(f'[RPA][ERROR] - unknown {platform.system()} operating system to setup TagUI')

        if not os.path.isfile('rpa_python.zip'):
            print('[RPA][INFO] - downloading TagUI (~200MB) and unzipping to below folder...')
            print(f'[RPA][INFO] - {home_directory}')
            tagui_zip_url = f'{_TAGUI_RELEASE_BASE_URL}/{tagui_zip_file}'
            if not self._download_file(tagui_zip_url, f'{home_directory}/{tagui_zip_file}'):
                return False
            self._unzip_file(f'{home_directory}/{tagui_zip_file}', home_directory)
            if not os.path.isfile(f'{home_directory}/tagui/src/tagui'):
                return self._handle_error(f'[RPA][ERROR] - unable to unzip TagUI to {home_directory}')
        else:
            print('[RPA][INFO] - unzipping TagUI (~200MB) from rpa_python.zip to below folder...')
            print(f'[RPA][INFO] - {home_directory}')
            import shutil
            shutil.move('rpa_python.zip', f'{home_directory}/{tagui_zip_file}')
            if not os.path.isdir(f'{home_directory}/tagui'):
                os.mkdir(f'{home_directory}/tagui')
            self._unzip_file(f'{home_directory}/{tagui_zip_file}', f'{home_directory}/tagui')
            if not os.path.isfile(f'{home_directory}/tagui/src/tagui'):
                return self._handle_error(f'[RPA][ERROR] - unable to unzip TagUI to {home_directory}')

        if platform.system() == 'Windows':
            tagui_directory = f'{home_directory}/tagui'
        else:
            tagui_directory = f'{home_directory}/.tagui'
            if os.path.isdir(tagui_directory):
                os.rename(tagui_directory, f'{tagui_directory}_previous')
            os.rename(f'{home_directory}/tagui', tagui_directory)
            if os.path.isdir(f'{tagui_directory}_previous'):
                import shutil
                shutil.rmtree(f'{tagui_directory}_previous')

        zip_path = f'{home_directory}/{tagui_zip_file}'
        if os.path.isfile(zip_path):
            os.remove(zip_path)

        print('[RPA][INFO] - done. syncing TagUI with stable cutting edge version')
        if not self._sync_delta(tagui_directory):
            return False

        if platform.system() == 'Linux':
            return self._setup_linux(tagui_directory)
        elif platform.system() == 'Darwin':
            return self._setup_macos(tagui_directory)
        elif platform.system() == 'Windows':
            return self._setup_windows(tagui_directory, home_directory)
        return True

    def _sync_delta(self, base_directory: str) -> bool:
        if not base_directory:
            return False
        if os.path.isfile(f'{base_directory}/rpa_python_{__version__}'):
            return True
        delta_list = [
            'tagui', 'tagui.cmd', 'end_processes', 'end_processes.cmd',
            'tagui_header.js', 'tagui_parse.php', 'tagui.sikuli/tagui.py'
        ]
        for delta_file in delta_list:
            url = f'{_TAGUI_RAW_BASE_URL}/TagUI-Python/{delta_file}'
            dest = f'{base_directory}/src/{delta_file}'
            if not self._download_file(url, dest):
                return False
        if platform.system() in ['Linux', 'Darwin']:
            os.system(f'chmod -R 755 "{base_directory}/src/tagui" > /dev/null 2>&1')
            os.system(f'chmod -R 755 "{base_directory}/src/end_processes" > /dev/null 2>&1')
        self._io.dump_file(
            'TagUI installation files used by RPA for Python',
            f'{base_directory}/rpa_python_{__version__}'
        )
        return True

    def _setup_linux(self, tagui_directory: str) -> bool:
        if os.system(f'chmod -R 755 "{tagui_directory}" > /dev/null 2>&1') != 0:
            return self._handle_error('[RPA][ERROR] - unable to set permissions for .tagui folder')
        if os.system('php --version > /dev/null 2>&1') != 0:
            print('[RPA][INFO] - PHP is not installed by default on your Linux distribution')
            print('[RPA][INFO] - google how to install PHP (eg for Ubuntu, apt-get install php)')
            print('[RPA][INFO] - after that, TagUI ready for use in your Python environment')
            print('[RPA][INFO] - visual automation (optional) requires special setup on Linux,')
            print('[RPA][INFO] - see the link below to install OpenCV and Tesseract libraries')
            print('[RPA][INFO] - https://sikulix-2014.readthedocs.io/en/latest/newslinux.html')
            return False
        else:
            print('[RPA][INFO] - TagUI now ready for use in your Python environment')
            print('[RPA][INFO] - visual automation (optional) requires special setup on Linux,')
            print('[RPA][INFO] - see the link below to install OpenCV and Tesseract libraries')
            print('[RPA][INFO] - https://sikulix-2014.readthedocs.io/en/latest/newslinux.html')
        return True

    def _setup_macos(self, tagui_directory: str) -> bool:
        if os.system(f'chmod -R 755 "{tagui_directory}" > /dev/null 2>&1') != 0:
            return self._handle_error('[RPA][ERROR] - unable to set permissions for .tagui folder')
        if not self._patch_macos_phantomjs():
            return False
        if not self._patch_macos_python3():
            return False
        print('[RPA][INFO] - TagUI now ready for use in your Python environment')
        return True

    def _setup_windows(self, tagui_directory: str, home_directory: str) -> bool:
        php_exe = f'{tagui_directory}/src/php/php.exe'
        if os.system(f'"{php_exe}" -v > nul 2>&1') != 0:
            print('[RPA][INFO] - now installing missing Visual C++ Redistributable dependency')
            vcredist_path = f'{tagui_directory}/vcredist_x86.exe'
            if not os.path.isfile(vcredist_path):
                url = f'{_TAGUI_RAW_BASE_URL}/vcredist_x86.exe'
                if not self._download_file(url, vcredist_path):
                    return False
            os.system(f'"{vcredist_path}"')
            if os.system(f'"{php_exe}" -v > nul 2>&1') != 0:
                print('[RPA][INFO] - MSVCR110.dll is still missing, install vcredist_x86.exe from')
                print(f'[RPA][INFO] - the vcredist_x86.exe file in {home_directory}\\tagui or from')
                print('[RPA][INFO] - https://www.microsoft.com/en-us/download/details.aspx?id=30679')
                print('[RPA][INFO] - after that, TagUI ready for use in your Python environment')
                return False
            else:
                print('[RPA][INFO] - TagUI now ready for use in your Python environment')
        else:
            print('[RPA][INFO] - TagUI now ready for use in your Python environment')
        return True

    def _patch_macos_phantomjs(self) -> bool:
        if platform.system() != 'Darwin':
            return True
        tagui_src = f'{self._config.tagui_location}/.tagui/src'
        if os.path.isdir(f'{tagui_src}/phantomjs_old'):
            return True
        original_dir = os.getcwd()
        os.chdir(tagui_src)
        print('[RPA][INFO] - downloading latest PhantomJS to fix OpenSSL issue')
        self._download_file(
            f'{_TAGUI_RELEASE_BASE_URL}/phantomjs-2.1.1-macosx.zip',
            'phantomjs.zip'
        )
        if not os.path.isfile('phantomjs.zip'):
            os.chdir(original_dir)
            return self._handle_error('[RPA][ERROR] - unable to download latest PhantomJS v2.1.1')
        self._unzip_file('phantomjs.zip')
        os.rename('phantomjs', 'phantomjs_old')
        os.rename('phantomjs-2.1.1-macosx', 'phantomjs')
        self._io.safe_remove('phantomjs.zip')
        os.system('chmod -R 755 phantomjs > /dev/null 2>&1')
        os.chdir(original_dir)
        return True

    def _patch_macos_python3(self) -> bool:
        if platform.system() != 'Darwin':
            return True
        tagui_src = f'{self._config.tagui_location}/.tagui/src'
        if os.path.isfile(f'{tagui_src}/py3_patched'):
            return True
        if os.system('python --version > /dev/null 2>&1') == 0:
            return True
        if os.system('python3 --version > /dev/null 2>&1') != 0:
            return True
        patch_files = [
            f'{tagui_src}/casperjs/bin/casperjs',
            f'{tagui_src}/casperjs/tests/clitests/runtests.py',
            f'{tagui_src}/slimerjs/slimerjs.py',
        ]
        for patch_file in patch_files:
            content = self._io.load_file(patch_file)
            content = content.replace('#!/usr/bin/env python', '#!/usr/bin/env python3')
            self._io.dump_file(content, patch_file)
        self._io.dump_file('python updated to python 3', f'{tagui_src}/py3_patched')
        return True

    def _set_turbo_mode(self, turbo: bool) -> None:
        tagui_dir = self._config.get_tagui_directory()
        chrome_php = f'{tagui_dir}/src/tagui_chrome.php'
        header_js = f'{tagui_dir}/src/tagui_header.js'
        sikuli_py = f'{tagui_dir}/src/tagui.sikuli/tagui.py'
        if not turbo:
            self._io.dump_file(
                self._io.load_file(chrome_php).replace('$scan_period = 10000;', '$scan_period = 100000;'),
                chrome_php
            )
            self._io.dump_file(
                self._io.load_file(header_js)
                    .replace('function sleep(ms) {ms *= 0.1; //', 'function sleep(ms) { //')
                    .replace(
                        "chrome_step('Input.insertText',{text: value});};",
                        "for (var character = 0, length = value.length; character < length; character++) {\n"
                        "chrome_step('Input.dispatchKeyEvent',{type: 'char', text: value[character]});}};"
                    ),
                header_js
            )
            self._io.dump_file(
                self._io.load_file(sikuli_py).replace(
                    'scan_period = 0.05\n\n# teleport mouse instead of moving to target\nSettings.MoveMouseDelay = 0',
                    'scan_period = 0.5'
                ),
                sikuli_py
            )
        else:
            self._io.dump_file(
                self._io.load_file(chrome_php).replace('$scan_period = 100000;', '$scan_period = 10000;'),
                chrome_php
            )
            self._io.dump_file(
                self._io.load_file(header_js)
                    .replace('function sleep(ms) { //', 'function sleep(ms) {ms *= 0.1; //')
                    .replace(
                        "for (var character = 0, length = value.length; character < length; character++) {\n"
                        "chrome_step('Input.dispatchKeyEvent',{type: 'char', text: value[character]});}};",
                        "chrome_step('Input.insertText',{text: value});};"
                    ),
                header_js
            )
            self._io.dump_file(
                self._io.load_file(sikuli_py).replace(
                    'scan_period = 0.5',
                    'scan_period = 0.05\n\n# teleport mouse instead of moving to target\nSettings.MoveMouseDelay = 0'
                ),
                sikuli_py
            )

    def init(self, visual_automation: bool = False, chrome_browser: bool = True,
             headless_mode: bool = False, turbo_mode: bool = False) -> bool:
        if self._started:
            return self._handle_error('[RPA][ERROR] - use close() before using init() again')
        self._id = 0
        self._init_directory = ''
        tagui_directory = self._config.get_tagui_directory()
        tagui_executable = self._config.get_tagui_executable()
        end_processes = self._config.get_end_processes_executable()
        if not os.path.isfile(tagui_executable):
            if not self.setup():
                return False
        if not self._sync_delta(tagui_directory):
            return False
        if platform.system() == 'Darwin':
            if not self._patch_macos_phantomjs():
                return False
            if not self._patch_macos_python3():
                return False
        if visual_automation:
            shell_silencer = '> nul 2>&1' if platform.system() == 'Windows' else '> /dev/null 2>&1'
            if os.system(f'java -version {shell_silencer}') != 0:
                print('[RPA][INFO] - to use visual automation mode, OpenJDK v8 (64-bit) or later is required')
                print('[RPA][INFO] - download from Amazon Corretto\'s website - https://aws.amazon.com/corretto')
                return False
            else:
                os.system('java -version > java_version.txt 2>&1')
                java_info = self._io.load_file('java_version.txt').lower()
                self._io.safe_remove('java_version.txt')
                if '64 bit' not in java_info and '64-bit' not in java_info:
                    print('[RPA][INFO] - to use visual automation mode, OpenJDK v8 (64-bit) or later is required')
                    print('[RPA][INFO] - download from Amazon Corretto\'s website - https://aws.amazon.com/corretto')
                    return False
                else:
                    sikulix_folder = f'{tagui_directory}/src/sikulix'
                    if os.path.isfile(f'{sikulix_folder}/jython-standalone-2.7.1.jar'):
                        os.system(f'java -jar "{sikulix_folder}/sikulix.jar" -h {shell_silencer}')
            self._write_entry_flow(True)
        else:
            self._write_entry_flow(False)
        self._write_local_js()
        browser_option = 'chrome' if chrome_browser else ''
        if headless_mode:
            browser_option = 'headless'
        self._set_turbo_mode(turbo_mode)
        tagui_cmd = f'"{tagui_executable}" rpa_python {browser_option}'
        os.system(f'"{end_processes}"')
        try:
            self._process = subprocess.Popen(
                tagui_cmd, shell=True,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            while True:
                if self._process.poll() is not None:
                    print('[RPA][ERROR] - following happens when starting TagUI...')
                    print(f'\nThe following command is executed to start TagUI -\n{tagui_cmd}\n')
                    print('It leads to following output when starting TagUI -')
                    os.system(tagui_cmd)
                    print('')
                    self._visual = False
                    self._chrome = False
                    self._started = False
                    self._handle_error('')
                    return False
                tagui_out = self._read_line()
                if 'LIVE MODE - type done to quit' in tagui_out:
                    self._write_line('echo "[RPA][STARTED]"\n')
                    self._write_line(f'echo "[RPA][{self._id}] - listening for inputs"\n')
                    self._visual = visual_automation
                    self._chrome = chrome_browser
                    self._started = True
                    while self._started and not self._ready():
                        time.sleep(0.05)
                    if not self._started:
                        return self._handle_error('[RPA][ERROR] - TagUI process ended unexpectedly')
                    self._cleanup_files()
                    self._id += 1
                    self._init_directory = os.getcwd()
                    self._download_directory = os.getcwd()
                    return True
        except Exception as e:
            self._visual = False
            self._chrome = False
            self._started = False
            return self._handle_error(f'[RPA][ERROR] - {str(e)}')

    def close(self) -> bool:
        if not self._started:
            return self._handle_error('[RPA][ERROR] - use init() before using close()')
        try:
            if self._process is None or self._process.poll() is not None:
                self._visual = False
                self._chrome = False
                self._started = False
                return self._handle_error('[RPA][ERROR] - no active TagUI process to close()')
            self._write_line('echo "[RPA][FINISHED]"\n')
            self._write_line('done\n')
            while self._process.poll() is None:
                time.sleep(0.05)
            self._cleanup_files()
            if not self._config.debug:
                self._io.safe_remove('rpa_python.log')
                self._io.safe_remove('rpa_python.txt')
                if self._init_directory:
                    self._io.safe_remove(os.path.join(self._init_directory, 'rpa_python.log'))
                    self._io.safe_remove(os.path.join(self._init_directory, 'rpa_python.txt'))
            self._visual = False
            self._chrome = False
            self._started = False
            return True
        except Exception as e:
            self._visual = False
            self._chrome = False
            self._started = False
            return self._handle_error(f'[RPA][ERROR] - {str(e)}')

    def send(self, instruction: Optional[str] = None) -> bool:
        if not self._started:
            return self._handle_error('[RPA][ERROR] - use init() before using send()')
        if instruction is None or instruction == '':
            return True
        try:
            if self._process is None or self._process.poll() is not None:
                self._visual = False
                self._chrome = False
                self._started = False
                return self._handle_error('[RPA][ERROR] - no active TagUI process to send()')
            instruction = (instruction.replace('\\', '\\\\').replace('\n', '\\n')
                           .replace('\r', '\\r').replace('\t', '\\t')
                           .replace('\a', '\\a').replace('\b', '\\b')
                           .replace('\f', '\\f').replace('[BACKSLASH_QUOTE]', "\\'"))
            echo_safe = instruction.replace('"', '\\"')
            self._write_line(f'echo "[RPA][{self._id}] - {echo_safe}"\n')
            self._write_line(f'{instruction}\n')
            self._write_line(f'echo "[RPA][{self._id}] - listening for inputs"\n')
            while self._started and not self._ready():
                time.sleep(0.05)
            if not self._started:
                return self._handle_error('[RPA][ERROR] - TagUI process ended unexpectedly')
            self._id += 1
            return True
        except Exception as e:
            return self._handle_error(f'[RPA][ERROR] - {str(e)}')

    def _check_visual_required(self, identifier: str) -> bool:
        if identifier.lower() in ['page.png', 'page.bmp']:
            if not self._visual:
                self._handle_error('[RPA][ERROR] - page.png / page.bmp requires init(visual_automation = True)')
                return False
            return True
        if identifier.lower().endswith(('.png', '.bmp')):
            if not self._visual:
                self._handle_error(f'[RPA][ERROR] - {identifier} identifier requires init(visual_automation = True)')
                return False
            return True
        if identifier.startswith('(') and identifier.endswith(')'):
            if len(identifier.split(',')) in [2, 3]:
                if not any(c.isalpha() for c in identifier):
                    if not self._visual:
                        self._handle_error('[RPA][ERROR] - x, y coordinates require init(visual_automation = True)')
                        return False
                    return True
        return True

    def exist(self, identifier: Optional[str] = None) -> bool:
        if not self._started:
            self._handle_error('[RPA][ERROR] - use init() before using exist()')
            return False
        if identifier is None or identifier == '':
            return False
        if not self._check_visual_required(identifier):
            return False
        if identifier.lower() in ['page.png', 'page.bmp'] and self._visual:
            return True
        if identifier.startswith('(') and identifier.endswith(')') and self._visual:
            return True
        self.send(f'exist_result = exist(\'{self._escape_xpath_quote(identifier)}\').toString()')
        self.send('dump exist_result to rpa_python.txt')
        return self._output() == 'true'

    def present(self, identifier: Optional[str] = None) -> bool:
        if not self._started:
            self._handle_error('[RPA][ERROR] - use init() before using present()')
            return False
        if identifier is None or identifier == '':
            return False
        if not self._check_visual_required(identifier):
            return False
        if identifier.lower() in ['page.png', 'page.bmp'] and self._visual:
            return True
        if identifier.startswith('(') and identifier.endswith(')') and self._visual:
            return True
        self.send(f'present_result = present(\'{self._escape_xpath_quote(identifier)}\').toString()')
        self.send('dump present_result to rpa_python.txt')
        return self._output() == 'true'

    def count(self, identifier: Optional[str] = None) -> int:
        if not self._started:
            self._handle_error('[RPA][ERROR] - use init() before using count()')
            return 0
        if identifier is None or identifier == '':
            return 0
        if not self._chrome:
            self._handle_error('[RPA][ERROR] - count() requires init(chrome_browser = True)')
            return 0
        self.send(f'count_result = count(\'{self._escape_xpath_quote(identifier)}\').toString()')
        self.send('dump count_result to rpa_python.txt')
        result = self._output()
        return int(result) if result else 0

    def url(self, webpage_url: Optional[str] = None):
        if not self._started:
            self._handle_error('[RPA][ERROR] - use init() before using url()')
            return False
        if not self._chrome:
            self._handle_error('[RPA][ERROR] - url() requires init(chrome_browser = True)')
            return False
        if webpage_url is not None and webpage_url != '':
            if webpage_url.lower().startswith('www.'):
                webpage_url = 'https://' + webpage_url
            if webpage_url.startswith(('http://', 'https://')):
                if not self.send(self._escape_single_quote(webpage_url)):
                    return False
                return True
            else:
                self._handle_error('[RPA][ERROR] - URL does not begin with http:// or https:// ')
                return False
        else:
            self.send('dump url() to rpa_python.txt')
            return self._output()

    def _click_action(self, action: str, identifier, test_coordinate=None):
        if not self._started:
            return self._handle_error(f'[RPA][ERROR] - use init() before using {action}()')
        if identifier is None or identifier == '':
            return self._handle_error(f'[RPA][ERROR] - target missing for {action}()')
        if test_coordinate is not None and isinstance(test_coordinate, int):
            identifier = self.coord(identifier, test_coordinate)
        if not self.exist(identifier):
            return self._handle_error(f'[RPA][ERROR] - cannot find {identifier}')
        return self.send(f'{action} {self._escape_xpath_quote(identifier)}')

    def click(self, identifier, test_coordinate=None):
        return self._click_action('click', identifier, test_coordinate)

    def rclick(self, identifier, test_coordinate=None):
        return self._click_action('rclick', identifier, test_coordinate)

    def dclick(self, identifier, test_coordinate=None):
        return self._click_action('dclick', identifier, test_coordinate)

    def hover(self, identifier, test_coordinate=None):
        return self._click_action('hover', identifier, test_coordinate)

    def type(self, identifier, text_to_type=None, test_coordinate=None):
        if not self._started:
            return self._handle_error('[RPA][ERROR] - use init() before using type()')
        if identifier is None or identifier == '':
            return self._handle_error('[RPA][ERROR] - target missing for type()')
        if text_to_type is None or text_to_type == '':
            return self._handle_error('[RPA][ERROR] - text missing for type()')
        if test_coordinate is not None and isinstance(text_to_type, int):
            identifier = self.coord(identifier, text_to_type)
            text_to_type = test_coordinate
        if not self.exist(identifier):
            return self._handle_error(f'[RPA][ERROR] - cannot find {identifier}')
        return self.send(f'type {self._escape_xpath_quote(identifier)} as {self._escape_single_quote(text_to_type)}')

    def select(self, identifier, option_value=None, test_coord1=None, test_coord2=None):
        if not self._started:
            return self._handle_error('[RPA][ERROR] - use init() before using select()')
        if identifier is None or identifier == '':
            return self._handle_error('[RPA][ERROR] - target missing for select()')
        if option_value is None or option_value == '':
            return self._handle_error('[RPA][ERROR] - option value missing for select()')
        if identifier.lower() in ['page.png', 'page.bmp'] or option_value.lower() in ['page.png', 'page.bmp']:
            return self._handle_error('[RPA][ERROR] - page.png / page.bmp identifiers invalid for select()')
        if test_coord1 is not None and test_coord2 is not None and \
           isinstance(option_value, int) and isinstance(test_coord2, int):
            identifier = self.coord(identifier, option_value)
            option_value = self.coord(test_coord1, test_coord2)
        if not self._check_visual_required(identifier):
            return False
        if not self.exist(identifier):
            return self._handle_error(f'[RPA][ERROR] - cannot find {identifier}')
        return self.send(
            f'select {self._escape_xpath_quote(identifier)} as {self._escape_single_quote(option_value)}'
        )

    def read(self, identifier, test_coord1=None, test_coord2=None, test_coord3=None):
        if not self._started:
            self._handle_error('[RPA][ERROR] - use init() before using read()')
            return ''
        if identifier is None or identifier == '':
            self._handle_error('[RPA][ERROR] - target missing for read()')
            return ''
        if test_coord1 is not None and isinstance(test_coord1, int):
            if test_coord2 is not None and isinstance(test_coord2, int):
                if test_coord3 is not None and isinstance(test_coord3, int):
                    identifier = f'{self.coord(identifier, test_coord1)}-{self.coord(test_coord2, test_coord3)}'
        if identifier.lower() != 'page' and not self.exist(identifier):
            self._handle_error(f'[RPA][ERROR] - cannot find {identifier}')
            return ''
        self.send(f'read {self._escape_xpath_quote(identifier)} to read_result')
        self.send('dump read_result to rpa_python.txt')
        return self._output()

    def snap(self, identifier, filename_to_save=None, test_coord1=None, test_coord2=None, test_coord3=None):
        if not self._started:
            return self._handle_error('[RPA][ERROR] - use init() before using snap()')
        if identifier is None or identifier == '':
            return self._handle_error('[RPA][ERROR] - target missing for snap()')
        if filename_to_save is None or filename_to_save == '':
            return self._handle_error('[RPA][ERROR] - filename missing for snap()')
        if test_coord2 is not None and test_coord3 is None:
            return self._handle_error('[RPA][ERROR] - filename missing for snap()')
        if isinstance(identifier, int) and isinstance(filename_to_save, int):
            if test_coord1 is not None and isinstance(test_coord1, int):
                if test_coord2 is not None and isinstance(test_coord2, int):
                    if test_coord3 is not None and test_coord3 != '':
                        identifier = f'{self.coord(identifier, filename_to_save)}-{self.coord(test_coord1, test_coord2)}'
                        filename_to_save = test_coord3
        if identifier.lower() != 'page' and not self.exist(identifier):
            return self._handle_error(f'[RPA][ERROR] - cannot find {identifier}')
        return self.send(f'snap {self._escape_xpath_quote(identifier)} to {self._escape_single_quote(filename_to_save)}')

    def table(self, identifier, filename_to_save=None):
        if not self._started:
            return self._handle_error('[RPA][ERROR] - use init() before using table()')
        if identifier is None or identifier == '':
            return self._handle_error('[RPA][ERROR] - target missing for table()')
        if filename_to_save is None or filename_to_save == '':
            return self._handle_error('[RPA][ERROR] - filename missing for table()')
        identifier = str(identifier)
        if not self.exist(identifier):
            return self._handle_error(f'[RPA][ERROR] - cannot find {identifier}')
        return self.send(f'table {self._escape_xpath_quote(identifier)} to {self._escape_single_quote(filename_to_save)}')

    def upload(self, identifier, filename_to_upload=None):
        if not self._started:
            return self._handle_error('[RPA][ERROR] - use init() before using upload()')
        if identifier is None or identifier == '':
            return self._handle_error('[RPA][ERROR] - target missing for upload()')
        if filename_to_upload is None or filename_to_upload == '':
            return self._handle_error('[RPA][ERROR] - filename missing for upload()')
        if not self.exist(identifier):
            return self._handle_error(f'[RPA][ERROR] - cannot find {identifier}')
        return self.send(f'upload {self._escape_xpath_quote(identifier)} as {self._escape_single_quote(filename_to_upload)}')

    def title(self) -> str:
        if not self._started:
            self._handle_error('[RPA][ERROR] - use init() before using title()')
            return ''
        if not self._chrome:
            self._handle_error('[RPA][ERROR] - title() requires init(chrome_browser = True)')
            return ''
        self.send('dump title() to rpa_python.txt')
        return self._output()

    def text(self) -> str:
        if not self._started:
            self._handle_error('[RPA][ERROR] - use init() before using text()')
            return ''
        if not self._chrome:
            self._handle_error('[RPA][ERROR] - text() requires init(chrome_browser = True)')
            return ''
        self.send('dump text() to rpa_python.txt')
        return self._output()

    def timer(self) -> float:
        if not self._started:
            self._handle_error('[RPA][ERROR] - use init() before using timer()')
            return 0.0
        self.send('dump timer() to rpa_python.txt')
        result = self._output()
        return float(result) if result else 0.0

    def frame(self, main_frame=None, sub_frame=None):
        if not self._started:
            return self._handle_error('[RPA][ERROR] - use init() before using frame()')
        if not self._chrome:
            return self._handle_error('[RPA][ERROR] - frame() requires init(chrome_browser = True)')
        self.send('js chrome_step("Runtime.evaluate", {expression: "mainframe_context = null"})')
        self.send('js chrome_step("Runtime.evaluate", {expression: "subframe_context = null"})')
        self.send('js chrome_context = "document"; frame_step_offset_x = 0; frame_step_offset_y = 0;')
        if main_frame is None or main_frame == '':
            return True
        frame_id = f'(//frame|//iframe)[@name="{main_frame}" or @id="{main_frame}"]'
        if not self.exist(frame_id):
            return self._handle_error(f'[RPA][ERROR] - cannot find frame with @name or @id as \'{main_frame}\'')
        self.send('js new_context = "mainframe_context"')
        self.send(f'js frame_xpath = \'(//frame|//iframe)[@name="{main_frame}" or @id="{main_frame}"]\'')
        self.send('js frame_rect = chrome.getRect(xps666(frame_xpath))')
        self.send('js frame_step_offset_x = frame_rect.left; frame_step_offset_y = frame_rect.top;')
        self.send('js chrome_step("Runtime.evaluate", {expression: new_context + " = document.evaluate(\'" + frame_xpath + "\'," + chrome_context + ",null,XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,null).snapshotItem(0).contentDocument"})')
        self.send('js chrome_context = new_context')
        if sub_frame is not None and sub_frame != '':
            frame_id = f'(//frame|//iframe)[@name="{sub_frame}" or @id="{sub_frame}"]'
            if not self.exist(frame_id):
                return self._handle_error(f'[RPA][ERROR] - cannot find sub frame with @name or @id as \'{sub_frame}\'')
            self.send('js new_context = "subframe_context"')
            self.send(f'js frame_xpath = \'(//frame|//iframe)[@name="{sub_frame}" or @id="{sub_frame}"]\'')
            self.send('js frame_rect = chrome.getRect(xps666(frame_xpath))')
            self.send('js frame_step_offset_x = frame_rect.left; frame_step_offset_y = frame_rect.top;')
            self.send('js chrome_step("Runtime.evaluate", {expression: new_context + " = document.evaluate(\'" + frame_xpath + "\'," + chrome_context + ",null,XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,null).snapshotItem(0).contentDocument"})')
            self.send('js chrome_context = new_context')
        return True

    def popup(self, string_in_url=None):
        if not self._started:
            return self._handle_error('[RPA][ERROR] - use init() before using popup()')
        if not self._chrome:
            return self._handle_error('[RPA][ERROR] - popup() requires init(chrome_browser = True)')
        self.send('js if (chrome_targetid !== "") {found_targetid = chrome_targetid; chrome_targetid = ""; chrome_step("Target.detachFromTarget", {sessionId: found_targetid});}')
        if string_in_url is None or string_in_url == '':
            return True
        self.send('js found_targetid = ""; chrome_targets = []; ws_message = chrome_step("Target.getTargets", {});')
        self.send('js try {ws_json = JSON.parse(ws_message); if (ws_json.result.targetInfos) chrome_targets = ws_json.result.targetInfos; else chrome_targets = [];} catch (e) {chrome_targets = [];}')
        self.send(f'js chrome_targets.forEach(function(target) {{if (target.url.indexOf("{string_in_url}") !== -1) found_targetid = target.targetId;}})')
        self.send('js if (found_targetid !== "") {ws_message = chrome_step("Target.attachToTarget", {targetId: found_targetid}); try {ws_json = JSON.parse(ws_message); if (ws_json.result.sessionId !== "") found_targetid = ws_json.result.sessionId; else found_targetid = "";} catch (e) {found_targetid = "";}}')
        self.send('js chrome_targetid = found_targetid')
        self.send('dump chrome_targetid to rpa_python.txt')
        popup_result = self._output()
        if popup_result != '':
            return True
        return self._handle_error(f'[RPA][ERROR] - cannot find popup tab containing URL string \'{string_in_url}\'')

    def dom(self, statement_to_run=None):
        if not self._started:
            self._handle_error('[RPA][ERROR] - use init() before using dom()')
            return ''
        if statement_to_run is None or statement_to_run == '':
            self._handle_error('[RPA][ERROR] - statement(s) missing for dom()')
            return ''
        if not self._chrome:
            self._handle_error('[RPA][ERROR] - dom() requires init(chrome_browser = True)')
            return ''
        self.send(f'dom {statement_to_run}')
        self.send('dump dom_result to rpa_python.txt')
        return self._output()

    def keyboard(self, keys_and_modifiers=None):
        if not self._started:
            return self._handle_error('[RPA][ERROR] - use init() before using keyboard()')
        if keys_and_modifiers is None or keys_and_modifiers == '':
            return self._handle_error('[RPA][ERROR] - keys to type missing for keyboard()')
        if not self._visual:
            return self._handle_error('[RPA][ERROR] - keyboard() requires init(visual_automation = True)')
        return self.send(f'keyboard {self._escape_single_quote(keys_and_modifiers)}')

    def mouse(self, mouse_action=None):
        if not self._started:
            return self._handle_error('[RPA][ERROR] - use init() before using mouse()')
        if mouse_action is None or mouse_action == '':
            return self._handle_error('[RPA][ERROR] - \'down\' / \'up\' missing for mouse()')
        if not self._visual:
            return self._handle_error('[RPA][ERROR] - mouse() requires init(visual_automation = True)')
        if mouse_action.lower() not in ('down', 'up'):
            return self._handle_error('[RPA][ERROR] - \'down\' / \'up\' missing for mouse()')
        return self.send(f'mouse {mouse_action}')

    def vision(self, command_to_run=None):
        if not self._started:
            return self._handle_error('[RPA][ERROR] - use init() before using vision()')
        if command_to_run is None or command_to_run == '':
            return self._handle_error('[RPA][ERROR] - command(s) missing for vision()')
        if not self._visual:
            return self._handle_error('[RPA][ERROR] - vision() requires init(visual_automation = True)')
        return self.send(f'vision {command_to_run}')

    def mouse_xy(self) -> str:
        if not self._started:
            self._handle_error('[RPA][ERROR] - use init() before using mouse_xy()')
            return ''
        if not self._visual:
            self._handle_error('[RPA][ERROR] - mouse_xy() requires init(visual_automation = True)')
            return ''
        self.send('dump mouse_xy() to rpa_python.txt')
        return self._output()

    def mouse_x(self) -> int:
        if not self._started:
            self._handle_error('[RPA][ERROR] - use init() before using mouse_x()')
            return 0
        if not self._visual:
            self._handle_error('[RPA][ERROR] - mouse_x() requires init(visual_automation = True)')
            return 0
        self.send('dump mouse_x() to rpa_python.txt')
        result = self._output()
        return int(result) if result else 0

    def mouse_y(self) -> int:
        if not self._started:
            self._handle_error('[RPA][ERROR] - use init() before using mouse_y()')
            return 0
        if not self._visual:
            self._handle_error('[RPA][ERROR] - mouse_y() requires init(visual_automation = True)')
            return 0
        self.send('dump mouse_y() to rpa_python.txt')
        result = self._output()
        return int(result) if result else 0

    def clipboard(self, text_to_put=None):
        if not self._started:
            return self._handle_error('[RPA][ERROR] - use init() before using clipboard()')
        if not self._visual:
            return self._handle_error('[RPA][ERROR] - clipboard() requires init(visual_automation = True)')
        if text_to_put is None:
            self.send('dump clipboard() to rpa_python.txt')
            return self._output()
        return self.send(f"js clipboard('{text_to_put.replace(chr(39), '[BACKSLASH_QUOTE]')}')")

    def focus(self, app_to_focus=None):
        if app_to_focus is None or app_to_focus == '':
            return self._handle_error('[RPA][ERROR] - app to focus missing for focus()')
        if platform.system() == 'Windows':
            if not os.path.isfile('sendKeys.bat'):
                url = f'{_TAGUI_RELEASE_BASE_URL}/sendKeys.bat'
                if not self._download_file(url, 'sendKeys.bat'):
                    return self._handle_error('[RPA][ERROR] - cannot download sendKeys.bat for focus()')
            if os.system(f'sendKeys.bat "{app_to_focus}" "" > nul 2>&1') == 0:
                return True
            return self._handle_error(f'[RPA][ERROR] - {app_to_focus} not found for focus()')
        elif platform.system() == 'Darwin':
            if os.system(f'osascript -e \'tell application "{app_to_focus}" to activate\' > /dev/null 2>&1') == 0:
                return True
            return self._handle_error(f'[RPA][ERROR] - {app_to_focus} not found for focus()')
        else:
            return self._handle_error('[RPA][ERROR] - Linux not supported for focus()')

    def download_location(self, location=None):
        if not self._started:
            return self._handle_error('[RPA][ERROR] - use init() before using download_location()')
        if location is None:
            return self._download_directory
        if "'" in location:
            return self._handle_error('[RPA][ERROR] - single quote in location not supported here')
        if platform.system() == 'Windows':
            location = location.replace('/', '\\')
        if not self.send(f"chrome_step('Page.setDownloadBehavior',{{behavior: 'allow', downloadPath: '{location}'}});"):
            return False
        self._download_directory = location
        return True

    def timeout(self, timeout_in_seconds=None):
        if not self._started:
            self._handle_error('[RPA][ERROR] - use init() before using timeout()')
            return False
        if timeout_in_seconds is None:
            return self._config.timeout
        self._config.timeout = float(timeout_in_seconds)
        return self.send(f'timeout {timeout_in_seconds}')

    @staticmethod
    def coord(x_coordinate=0, y_coordinate=0):
        return f'({x_coordinate},{y_coordinate})'

    @staticmethod
    def wait(delay_in_seconds=5.0):
        time.sleep(float(delay_in_seconds))
        return True

    @staticmethod
    def echo(text_to_echo=''):
        print(text_to_echo)
        return True

    @staticmethod
    def check(condition_to_check=None, text_if_true='', text_if_false=''):
        if condition_to_check is None:
            print('[RPA][ERROR] - condition missing for check()')
            return False
        if condition_to_check:
            print(text_if_true)
        else:
            print(text_if_false)
        return True

    @staticmethod
    def ask(text_to_prompt=''):
        return input(text_to_prompt + (' ' if text_to_prompt else ''))

    @staticmethod
    def get_text(source_text=None, left=None, right=None, count=1):
        if source_text is None or left is None or right is None:
            return ''
        left_position = source_text.find(left)
        if left_position == -1:
            return ''
        right_position = source_text.find(right, left_position + 1)
        if right_position == -1:
            return ''
        occurrence = 1
        while occurrence < count:
            occurrence += 1
            left_position = source_text.find(left, right_position + 1)
            if left_position == -1:
                return ''
            right_position = source_text.find(right, left_position + 1)
            if right_position == -1:
                return ''
        return source_text[left_position + len(left):right_position].strip()

    @staticmethod
    def del_chars(source_text=None, characters=None):
        if source_text is None:
            return ''
        if characters is None:
            return source_text
        for char in characters:
            source_text = source_text.replace(char, '')
        return source_text

    @staticmethod
    def load(filename_to_load=None):
        if filename_to_load is None or filename_to_load == '':
            print('[RPA][ERROR] - filename missing for load()')
            return ''
        if not os.path.isfile(filename_to_load):
            print(f'[RPA][ERROR] - cannot load file {filename_to_load}')
            return ''
        return IOHelper.load_file(filename_to_load)

    @staticmethod
    def dump(text_to_dump=None, filename_to_save=None):
        if text_to_dump is None:
            print('[RPA][ERROR] - text missing for dump()')
            return False
        if filename_to_save is None or filename_to_save == '':
            print('[RPA][ERROR] - filename missing for dump()')
            return False
        IOHelper.dump_file(text_to_dump, filename_to_save)
        return True

    @staticmethod
    def write(text_to_write=None, filename_to_save=None):
        if text_to_write is None:
            print('[RPA][ERROR] - text missing for write()')
            return False
        if filename_to_save is None or filename_to_save == '':
            print('[RPA][ERROR] - filename missing for write()')
            return False
        IOHelper.append_file(text_to_write, filename_to_save)
        return True

    @staticmethod
    def download(download_url=None, filename_to_save=None):
        if download_url is None or download_url == '':
            print('[RPA][ERROR] - download URL missing for download()')
            return False
        if filename_to_save is None or filename_to_save == '':
            tokens = download_url.split('/')
            filename_to_save = tokens[-1]
        if os.path.isfile(filename_to_save):
            os.remove(filename_to_save)
        try:
            import urllib.request
            urllib.request.urlretrieve(download_url, filename_to_save)
        except Exception as e:
            print(str(e))
            print(f'[RPA][ERROR] - failed downloading from {download_url}...')
            return False
        if os.path.isfile(filename_to_save):
            return True
        print(f'[RPA][ERROR] - failed downloading to {filename_to_save}')
        return False

    @staticmethod
    def unzip(file_to_unzip=None, unzip_location=None):
        if file_to_unzip is None or file_to_unzip == '':
            print('[RPA][ERROR] - filename missing for unzip()')
            return False
        if not os.path.isfile(file_to_unzip):
            print('[RPA][ERROR] - file specified missing for unzip()')
            return False
        with zipfile.ZipFile(file_to_unzip, 'r') as zf:
            if unzip_location:
                zf.extractall(unzip_location)
            else:
                zf.extractall()
        return True

    @staticmethod
    def run(command_to_run=None):
        if command_to_run is None or command_to_run == '':
            print('[RPA][ERROR] - command(s) missing for run()')
            return ''
        delimiter = ' & ' if platform.system() == 'Windows' else '; '
        return subprocess.check_output(
            command_to_run + delimiter + 'exit 0',
            stderr=subprocess.STDOUT,
            shell=True
        ).decode('utf-8')

    @staticmethod
    def telegram(telegram_id=None, text_to_send=None, custom_endpoint=None):
        if telegram_id is None or telegram_id == '':
            print('[RPA][ERROR] - Telegram ID missing for telegram()')
            return False
        if text_to_send is None or text_to_send == '':
            print('[RPA][ERROR] - text message missing for telegram()')
            return False
        telegram_id = str(telegram_id)
        endpoint = custom_endpoint if custom_endpoint else _TELEGRAM_BOT_ENDPOINT
        params = {'chat_id': telegram_id, 'text': text_to_send}
        try:
            import json
            import urllib.request
            import urllib.parse
            full_url = endpoint + '/sendMessage.php?' + urllib.parse.urlencode(params)
            response = urllib.request.urlopen(full_url).read()
            return json.loads(response)['ok']
        except Exception:
            return False

    def bin(self, file_to_bin=None, password=None, server=_BIN_SERVER_URL):
        if not self._started:
            self._handle_error('[RPA][ERROR] - use init() before using bin()')
            return ''
        if file_to_bin is None or file_to_bin == '':
            self._handle_error('[RPA][ERROR] - file_to_bin required for bin()')
            return ''
        file_to_bin = os.path.abspath(file_to_bin)
        if not os.path.isfile(file_to_bin):
            self._handle_error(f'[RPA][ERROR] - cannot find {file_to_bin}')
            return ''
        original_url = self.url()
        self.url(server)
        if not self.exist('//*[@id = "message"]'):
            self._handle_error(f'[RPA][ERROR] - cannot connect to {server}')
            return ''
        file_head, file_tail = os.path.split(file_to_bin)
        self.type('//*[@id = "message"]', file_tail)
        if password is not None:
            self.type('//*[@id = "passwordinput"]', password)
        self.click('//*[@id = "attach"]')
        self.upload('#file', file_to_bin)
        self.click('//*[@id = "sendbutton"]')
        bin_url = self.read('//*[@id = "pastelink"]/a/@href')
        if bin_url == '':
            self._handle_error(f'[RPA][ERROR] - failed uploading to {server}')
        if original_url != 'about:blank':
            self.url(original_url)
        return bin_url

    def pack(self) -> bool:
        print('[RPA][INFO] - pack() is to deploy RPA for Python to a computer without internet')
        print('[RPA][INFO] - update() is to update an existing installation deployed from pack()')
        print('[RPA][INFO] - detecting and zipping your TagUI installation to rpa_python.zip ...')
        if self._started:
            if not self.close():
                return False
        if not self.init(False, False):
            return False
        if not self.close():
            return False
        if platform.system() == 'Windows':
            tagui_directory = f'{self._config.tagui_location}/tagui'
            vcredist_url = f'{_TAGUI_RAW_BASE_URL}/vcredist_x86.exe'
            if not self._download_file(vcredist_url, f'{tagui_directory}/vcredist_x86.exe'):
                return False
        else:
            tagui_directory = f'{self._config.tagui_location}/.tagui'
        sikulix_dir = f'{tagui_directory}/src/sikulix'
        jython_url = f'{_TAGUI_RELEASE_BASE_URL}/jython-standalone-2.7.1.jar'
        if not self._download_file(jython_url, f'{sikulix_dir}/jython-standalone-2.7.1.jar'):
            return False
        import shutil
        shutil.make_archive('rpa_python', 'zip', tagui_directory)
        shutil.copyfile(os.path.join(os.path.dirname(__file__), '..', '..', 'tagui.py'), 'rpa.py')
        print('[RPA][INFO] - done. copy rpa_python.zip and rpa.py to your target computer.')
        print('[RPA][INFO] - then install and use with import rpa as r followed by r.init()')
        return True

    def update(self) -> bool:
        print('[RPA][INFO] - pack() is to deploy RPA for Python to a computer without internet')
        print('[RPA][INFO] - update() is to update an existing installation deployed from pack()')
        print('[RPA][INFO] - downloading latest RPA for Python and TagUI files...')
        if not os.path.isdir('rpa_update'):
            os.mkdir('rpa_update')
        if not os.path.isdir('rpa_update/tagui.sikuli'):
            os.mkdir('rpa_update/tagui.sikuli')
        rpa_python_url = _TAGUI_RPA_RAW_URL
        if not self._download_file(rpa_python_url, 'rpa_update/rpa.py'):
            return False
        delta_list = [
            'tagui', 'tagui.cmd', 'end_processes', 'end_processes.cmd',
            'tagui_header.js', 'tagui_parse.php', 'tagui.sikuli/tagui.py'
        ]
        for delta_file in delta_list:
            url = f'{_TAGUI_RAW_BASE_URL}/TagUI-Python/{delta_file}'
            dest = f'rpa_update/{delta_file}'
            if not self._download_file(url, dest):
                return False
        import shutil
        shutil.make_archive('rpa_update', 'zip', 'rpa_update')
        update_py_header = (
            'import rpa as r\n'
            'import platform\n'
            'import base64\n'
            'import shutil\n'
            'import os\n\n'
            'rpa_update_zip = \\\n'
        )
        update_py_footer = '''\n
rpa_update_zip = rpa_update_zip.replace(" ","")
update_zip_file = open("update.zip","wb")
update_zip_file.write(base64.b64decode(rpa_update_zip))
update_zip_file.close()
if platform.system() == "Windows":
    base_directory = os.environ["APPDATA"] + "/tagui"
else:
    base_directory = os.path.expanduser("~") + "/.tagui"
shutil.unpack_archive("update.zip", base_directory)
print("[RPA][INFO] - done. your copy of RPA for Python is now updated")
'''
        update_zip_content = self._io.load_file('rpa_update.zip')
        update_zip_content = base64.b64encode(update_zip_content).decode('utf-8')
        import base64
        update_py = update_py_header + '\n'.join(
            update_zip_content[i:i + 80] for i in range(0, len(update_zip_content), 80)
        ) + update_py_footer
        self._io.dump_file(update_py, 'update.py')
        shutil.rmtree('rpa_update')
        self._io.safe_remove('rpa_update.zip')
        print('[RPA][INFO] - done. copy update.py to your target computer and run it there.')
        return True

    def debug(self, debug_mode: bool = True) -> None:
        self._config.debug = debug_mode

    def error(self, error_mode: bool = True) -> None:
        self._config.error_mode = error_mode

    def tagui_location(self, location: Optional[str] = None) -> str:
        if location is not None:
            self._config.tagui_location = location
        return self._config.tagui_location

    def snap_page(self, filename_to_save: str = 'page.png') -> bool:
        return self.snap('page.png', filename_to_save)

    def snap_element(self, identifier, filename_to_save: str = 'element.png') -> bool:
        return self.snap(identifier, filename_to_save)