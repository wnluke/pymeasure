#
# This file is part of the PyMeasure package.
#
# Copyright (c) 2013-2023 PyMeasure Developers
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

import logging
from warnings import warn

import pyvisa
import numpy as np

from .adapter import Adapter
from .protocol import ProtocolAdapter

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


# noinspection PyPep8Naming,PyUnresolvedReferences
class VISAAdapter(Adapter):
    """ Adapter class for the VISA library, using PyVISA to communicate with instruments.

    The workhorse of our library, used by most instruments.

    :param resource_name: A
        `VISA resource string <https://pyvisa.readthedocs.io/en/latest/introduction/names.html>`__
        or GPIB address integer that identifies the target of the connection
    :param visa_library: PyVISA VisaLibrary Instance, path of the VISA library or VisaLibrary spec
        string (``@py`` or ``@ivi``). If not given, the default for the platform will be used.
    :param preprocess_reply: An optional callable used to preprocess strings
        received from the instrument. The callable returns the processed string.

        .. deprecated:: 0.11
            Implement it in the instrument's `read` method instead.

    :param float query_delay: Time in s to wait after writing and before reading.

        .. deprecated:: 0.11
            Implement it in the instrument's `wait_for` method instead.

    :param log: Parent logger of the 'Adapter' logger.
    :param \\**kwargs: Keyword arguments for configuring the PyVISA connection.

    :Kwargs:
        Keyword arguments are used to configure the connection created by PyVISA. This is
        complicated by the fact that *which* arguments are valid depends on the interface (e.g.
        serial, GPIB, TCPI/IP, USB) determined by the current ``resource_name``.

        A flexible process is used to easily define reasonable *default values* for
        different instrument interfaces, but also enable the instrument user to *override any
        setting* if their situation demands it.

        A kwarg that names a pyVISA interface type (most commonly ``asrl``, ``gpib``, ``tcpip``, or
        ``usb``) is a dictionary with keyword arguments defining defaults specific to that
        interface. Example: ``asrl={'baud_rate': 4200}``.

        All other kwargs are either generally valid (e.g. ``timeout=500``) or override any default
        settings from the interface-specific entries above. For example, passing
        ``baud_rate=115200`` when connecting via a resource name ``ASRL1`` would override a
        default of 4200 defined as above.

        See :ref:`connection_settings` for how to tweak settings when *connecting* to an instrument.
        See :ref:`default_connection_settings` for how to best define default settings when
        *implementing an instrument*.
    """

    def __init__(self, resource_name, visa_library='', preprocess_reply=None,
                 query_delay=0, log=None, **kwargs):
        super().__init__(preprocess_reply=preprocess_reply, log=log)
        if query_delay:
            warn(("Parameter `query_delay` is deprecated. "
                  "Implement in Instrument's `wait_for` instead."),
                 FutureWarning)
            kwargs.setdefault("query_delay", query_delay)
        self.query_delay = query_delay
        if isinstance(resource_name, ProtocolAdapter):
            self.connection = resource_name
            self.connection.write_raw = self.connection.write_bytes
            self.read_bytes = self.connection.read_bytes
            return
        elif isinstance(resource_name, VISAAdapter):
            # Allow to reuse the connection.
            self.resource_name = getattr(resource_name, "resource_name", None)
            self.connection = resource_name.connection
            self.manager = resource_name.manager
            self.query_delay = resource_name.query_delay
            return
        elif isinstance(resource_name, int):
            resource_name = "GPIB0::%d::INSTR" % resource_name

        self.resource_name = resource_name
        self.manager = pyvisa.ResourceManager(visa_library)

        # Clean up kwargs considering the interface type matching resource_name
        if_type = self.manager.resource_info(self.resource_name).interface_type
        for key in list(kwargs.keys()):  # iterate over a copy of the keys as we modify kwargs
            # Remove all interface-specific kwargs:
            if key in pyvisa.constants.InterfaceType.__members__:
                if getattr(pyvisa.constants.InterfaceType, key) is if_type:
                    # For the present interface, dump contents into kwargs first if they are not
                    # present already. This way, it is possible to override default values with
                    # kwargs passed to Instrument.__init__()
                    for k, v in kwargs[key].items():
                        kwargs.setdefault(k, v)
                del kwargs[key]

        self.connection = self.manager.open_resource(
            resource_name,
            **kwargs
        )

    def close(self):
        """Close the connection.

        .. note::

            This closes the connection to the resource for all adapters using
            it currently (e.g. different adapters using the same GPIB line).
        """
        super().close()
        try:
            if self.manager.visalib.library_path == "unset":
                # if using the pyvisa-sim library the manager has to be also closed.
                # this works around https://github.com/pyvisa/pyvisa-sim/issues/82
                self.manager.close()
        except AttributeError:
            # AttributeError can occur during __del__ calling close
            pass

    def _write(self, command, **kwargs):
        """Write a string command to the instrument appending `write_termination`.

        :param str command: Command string to be sent to the instrument
            (without termination).
        :param \\**kwargs: Keyword arguments for the connection itself.
        """
        self.connection.write(command, **kwargs)

    def _write_bytes(self, content, **kwargs):
        """Write the bytes `content` to the instrument.

        :param bytes content: The bytes to write to the instrument.
        :param \\**kwargs: Keyword arguments for the connection itself.
        """
        self.connection.write_raw(content, **kwargs)

    def _read(self, **kwargs):
        """Read up to (excluding) `read_termination` or the whole read buffer.

        :param \\**kwargs: Keyword arguments for the connection itself.
        :returns str: ASCII response of the instrument (excluding read_termination).
        """
        return self.connection.read(**kwargs)

    def _read_bytes(self, count, break_on_termchar=False, **kwargs):
        """Read a certain number of bytes from the instrument.

        :param int count: Number of bytes to read. A value of -1 indicates to
            read from the whole read buffer until timeout.
        :param bool break_on_termchar: Stop reading at a termination character.
        :param \\**kwargs: Keyword arguments for the connection itself.
        :returns bytes: Bytes response of the instrument (including termination).
        """
        if count >= 0:
            return self.connection.read_bytes(count, break_on_termchar=break_on_termchar, **kwargs)
        elif break_on_termchar:
            return self.connection.read_raw(None, **kwargs)
        else:
            # pyvisa's `read_raw` reads until newline, if no termination_character defined
            # and if not configured to stop at a termination lane etc.
            # see https://github.com/pyvisa/pyvisa/issues/728
            result = bytearray()
            while True:
                try:
                    result.extend(self.connection.read_bytes(1))
                except pyvisa.errors.VisaIOError as exc:
                    if exc.error_code == pyvisa.constants.StatusCode.error_timeout:
                        return bytes(result)
                    raise

<<<<<<< HEAD
    def ask(self, command):
        """ Writes the command to the instrument and returns the resulting
        ASCII response
=======
    def __repr__(self):
        return self.visa_resource_name()
>>>>>>> power_supplies

        .. deprecated:: 0.11
           Call `Instrument.ask` instead.

        :param command: SCPI command string to be sent to the instrument
        :returns: String ASCII response of the instrument
        """
        warn("`Adapter.ask` is deprecated, call `Instrument.ask` instead.", FutureWarning)
        return self.connection.query(command)

    def ask_values(self, command, **kwargs):
        """ Writes a command to the instrument and returns a list of formatted
        values from the result. This leverages the `query_ascii_values` method
        in PyVISA.

        .. deprecated:: 0.11
            Call `Instrument.values` instead.

        :param command: SCPI command to be sent to the instrument
        :param \\**kwargs: Key-word arguments to pass onto `query_ascii_values`
        :returns: Formatted response of the instrument.
        """
<<<<<<< HEAD
        warn("`Adapter.ask_values` is deprecated, call `Instrument.values` instead.",
             FutureWarning)

        return self.connection.query_ascii_values(command, **kwargs)

    def binary_values(self, command, header_bytes=0, dtype=np.float32):
        """ Returns a numpy array from a query for binary data

        .. deprecated:: 0.11
            Call `Instrument.binary_values` instead.

=======
        return self.connection.read()

    def values(self, command, separator = ','):
        """ Writes a command to the instrument and returns a list of numerical
        values from the result.

        :param command: SCPI command to be sent to the instrument.
        :returns: A list of numerical values.
        """
        results = str(self.ask(command)).strip()
        results = results.split(separator)
        for result in results:
            try:
                result = float(result)
            except:
                pass # Keep as string
        return results

    def binary_values(self, command, header_bytes=0, dtype=np.float32):
        """ Returns a numpy array from a query for binary data

>>>>>>> power_supplies
        :param command: SCPI command to be sent to the instrument
        :param header_bytes: Integer number of bytes to ignore in header
        :param dtype: The NumPy data type to format the values with
        :returns: NumPy array of values
        """
        warn("`Adapter.binary_values` is deprecated, call `Instrument.binary_values` instead.",
             FutureWarning)
        self.connection.write(command)
        binary = self.connection.read_raw()
        # header = binary[:header_bytes]
        data = binary[header_bytes:]
        return np.fromstring(data, dtype=dtype)
<<<<<<< HEAD
=======

>>>>>>> power_supplies

    def write_binary_values(self, command, values, timeout=None, **kwargs):
        """ Write binary data to the instrument, e.g. waveform for signal generators

<<<<<<< HEAD
        This command is often used to transfer large set of data, eg. waveform for signal
        generators and the timeout parameter is very useful since VISA enforce a timeout also
        during write operation.
=======
    :param resource: VISA resource name that identifies the address.
    :param kwargs: Any valid key-word arguments for constructing a PyVISA instrument.
    """
    def __init__(self, resourceName, **kwargs):
        self.connection = visa.instrument(resourceName, **kwargs)

    def config(self, **kwargs):
        """ Reserve for future implementation."""
        log.warning("Class method config() not yet implemented! Do nothing.")
        pass

    def ask(self, command):
        """ Writes the command to the instrument and returns the resulting
        ASCII response

        :param command: SCPI command string to be sent to the instrument
        :returns: String ASCII response of the instrument
        """
        return self.connection.ask(command)

    def ask_values(self, command):
        """ Writes a command to the instrument and returns a list of formatted
        values from the result
>>>>>>> power_supplies

        :param command: SCPI command to be sent to the instrument
        :param values: iterable representing the binary values
        :param timeout: timeout in milliseconds, None to leave untouched
        :param kwargs: Key-word arguments to pass onto `write_binary_values`
        :returns: number of bytes written
        """

        oldtimeout = self.connection.timeout
        if not (timeout is None):
            self.connection.timeout = timeout

        try:
            return_value = super().write_binary_values(command, values, **kwargs)
        finally:
            self.connection.timeout = oldtimeout

        return return_value

    def wait_for_srq(self, timeout=25, delay=0.1):
        """ Block until a SRQ, and leave the bit high

        :param timeout: Timeout duration in seconds
        :param delay: Time delay between checking SRQ in seconds
        """
        self.connection.wait_for_srq(timeout * 1000)

<<<<<<< HEAD
    def flush_read_buffer(self):
        """ Flush and discard the input buffer

        As detailed by pyvisa, discard the read and receivee buffer contents
        and if data was present in the read buffer and no END-indicator was present,
        read from the device until encountering an END indicator (which causes loss of data).
=======
    def visa_resource_name(self):
        return "<VISAAdapter(resource='%s')>" % self.connection.resourceName

class VISAAdapter17(Adapter):
    """ Adapter class for VISA version 1.5 or above. Be inherited by class VISAAdapter.

    :param resource: VISA resource name that identifies the address.
    :param kwargs: Any valid key-word arguments for constructing a PyVISA instrument.
    """
    def __init__(self, resourceName, **kwargs):
        self.manager = visa.ResourceManager()
        safeKeywords = ['resource_name', 'timeout', 'term_chars',
                        'chunk_size', 'lock', 'delay', 'send_end',
                        'values_format']
        kwargsCopy = copy.deepcopy(kwargs)
        for key in kwargsCopy:
            if key not in safeKeywords:
                kwargs.pop(key)
        self.connection = self.manager.get_instrument(
                                resourceName,
                                **kwargs
                          )

    def config(self, is_binary = False, datatype = 'str',
                    container = np.array, converter = 's',
                    separator = ',', is_big_endian = False):
        """ Configurate the format of data transfer to and from the instrument.

        :param is_binary: If True, data is in binary format, otherwise ASCII.
        :param datatype: Data type.
        :param container: Return format. Any callable/type that takes an iterable.
        :param converter: String converter, used in dealing with ASCII data.
        :param separator: Delimiter of a series of data in ASCII.
        :param is_big_endian: Endianness.
>>>>>>> power_supplies
        """
        try:
            self.connection.flush(pyvisa.constants.BufferOperation.discard_read_buffer)
            self.connection.flush(pyvisa.constants.BufferOperation.discard_receive_buffer)
        except NotImplementedError:
            # NotImplementedError is raised when using resource types other than `asrl`
            # in conjunction with pyvisa-py.
            # Upstream issue: https://github.com/pyvisa/pyvisa-py/issues/348
            # fake discarding the read buffer by reading all available messages.
            timeout = self.connection.timeout
            self.connection.timeout = 0
            try:
                self.read_bytes(-1)
            except pyvisa.errors.VisaIOError:
                pass
            finally:
                self.connection.timeout = timeout

<<<<<<< HEAD
    def __repr__(self):
        return "<VISAAdapter(resource='%s')>" % self.connection.resource_name
=======
    def ask(self, command):
        """ Writes the command to the instrument and returns the resulting
        ASCII response

        :param command: SCPI command string to be sent to the instrument
        :returns: String ASCII response of the instrument
        """
        return self.connection.query(command)

    def ask_values(self, command):
        """ Writes a command to the instrument and returns a list of formatted
        values from the result. The format of the return is configurated by
        self.config().

        :param command: SCPI command to be sent to the instrument
        :returns: Formatted response of the instrument.
        """
        return self.connection.query_values(command)

    def visa_resource_name(self):
        return "<VISAAdapter(resource='%s')>" % self.connection.resource_name

    def wait_for_srq(self, timeout=25, delay=0.1):
        """ Blocks until a SRQ, and leaves the bit high

        :param timeout: Timeout duration in seconds
        :param delay: Time delay between checking SRQ in seconds
        """
        self.connection.wait_for_srq(timeout*1000)
>>>>>>> power_supplies
