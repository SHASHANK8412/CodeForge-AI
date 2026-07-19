import logging
from datetime import datetime

_logger = logging.getLogger("aiforge.performance")

MIT_TEMPLATE = """MIT License

Copyright (c) {year} {owner}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

APACHE_TEMPLATE = """                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   Copyright {year} {owner}

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

GPL_TEMPLATE = """                    GNU GENERAL PUBLIC LICENSE
                       Version 3, 29 June 2007

 Copyright (C) {year} {owner}

 Everyone is permitted to copy and distribute verbatim copies
 of this license document, but changing it is not allowed.

                            Preamble

  The GNU General Public License is a free, copyleft license for
software and other kinds of works.
  [GPL v3 Short Preamble Implementation]
  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.
"""


class LicenseGenerator:
    """
    Generates standard open-source license templates including MIT, Apache 2.0, and GPL v3.
    """

    def __init__(self) -> None:
        pass

    def generate_license(self, license_type: str = "MIT", owner: str = "AIForge") -> str:
        """
        Dynamically compiles the selected license.
        """
        _logger.info(f"Generating LICENSE template of type '{license_type}'...")
        year = datetime.now().year
        l_type = license_type.upper().strip()

        if "MIT" in l_type:
            content = MIT_TEMPLATE.format(year=year, owner=owner)
        elif "APACHE" in l_type:
            content = APACHE_TEMPLATE.format(year=year, owner=owner)
        elif "GPL" in l_type:
            content = GPL_TEMPLATE.format(year=year, owner=owner)
        else:
            _logger.warning(f"Unknown license type '{license_type}', defaulting to MIT")
            content = MIT_TEMPLATE.format(year=year, owner=owner)

        _logger.info("LICENSE generated successfully")
        return content
