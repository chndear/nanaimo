#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# This software is distributed under the terms of the MIT License.
#

import fixtures
import fixtures.simulators
import nanaimo
import nanaimo.serial
import nanaimo.jlink
import nanaimo.gtest
import os
import pytest
import asyncio


@pytest.mark.timeout(10)
def test_uart_monitor() -> None:
    """
    Verify the nanaimo.ConcurrentUartMonitor class using a mock serial port.
    """
    serial = fixtures.simulators.Serial(fixtures.FAKE_TEST_SUCCESS)
    last_line = fixtures.FAKE_TEST_SUCCESS[-1]
    with nanaimo.serial.ConcurrentUartMonitor(serial) as monitor:
        while True:
            line = monitor.readline()
            if line is None:
                os.sched_yield()
                continue
            elif line == last_line:
                break


@pytest.mark.asyncio
async def test_program_uploader() -> None:
    uploader = nanaimo.jlink.ProgramUploaderJLink(fixtures.get_mock_JLinkExe())
    assert 0 == await uploader.upload(fixtures.get_s32K144_jlink_script())


@pytest.mark.asyncio
async def test_program_uploader_failure() -> None:
    uploader = nanaimo.jlink.ProgramUploaderJLink(fixtures.get_mock_JLinkExe(), ['--simulate-error'])
    assert 0 != await uploader.upload(fixtures.get_s32K144_jlink_script())


@pytest.mark.asyncio
async def test_program_while_monitoring() -> None:
    scripts = fixtures.get_s32K144_jlink_scripts()
    uploader = nanaimo.jlink.ProgramUploaderJLink(fixtures.get_mock_JLinkExe())
    serial = fixtures.simulators.Serial(fixtures.FAKE_TEST_SUCCESS)
    uploads = 0
    with nanaimo.serial.ConcurrentUartMonitor(serial) as monitor:
        for script in scripts:
            serial.reset_mock()
            results = await asyncio.gather(
                nanaimo.gtest.Parser(10).read_test(monitor),
                uploader.upload(script)
            )
            assert 2 == len(results)

            for result in results:
                assert 0 == result
            uploads += 1
    assert uploads > 1


@pytest.mark.asyncio
async def test_failed_test() -> None:
    serial = fixtures.simulators.Serial(fixtures.FAKE_TEST_FAILURE)
    with nanaimo.serial.ConcurrentUartMonitor(serial) as monitor:
        assert 1 == await nanaimo.gtest.Parser(10).read_test(monitor)


@pytest.mark.asyncio
async def test_timeout_while_monitoring() -> None:
    serial = fixtures.simulators.Serial(['gibberish'])
    with nanaimo.serial.ConcurrentUartMonitor(serial) as monitor:
        assert 0 != await nanaimo.gtest.Parser(1.0).read_test(monitor)
