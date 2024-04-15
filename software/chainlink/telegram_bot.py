#!/usr/bin/env python3
import sys
import serial.tools.list_ports
from typing import Tuple
import logging
from splitflap_proto import splitflap_context

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger('httpx').setLevel(logging.WARNING)

logger = logging.getLogger('SplitFlap bot')


def list_ports() -> None:
    ports = list(sorted((p.device, p.description) for p in serial.tools.list_ports.comports()
                        if p.description and p.description != 'n/a'))
    device_length = max([0, *[len(device) for device, _ in ports]])
    fmt_str = '{:<%d} {}' % device_length
    for device, description in ports:  # type: Tuple[str, str]
        print(fmt_str.format(device, description))


def main(port: str, token: str) -> None:
    with splitflap_context(port) as s:
        application = Application.builder().token(token).build()

        async def handle_start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
            await update.message.reply_text('Split flap bot active.')

        async def handle_help(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
            await update.message.reply_markdown(f'You can change the text with `/flap text`.')

        async def handle_flap(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            try:
                logger.info(f'{update.message.from_user.name} set the text to "{" ".join(context.args)}"')
                s.set_text(' '.join(context.args))
            except Exception as e:
                logging.error('Unable to set split flap text.')
                await update.message.reply_markdown(f'There was an error changing text, `{e}`')

        application.add_handler(CommandHandler('start', handle_start))
        application.add_handler(CommandHandler('help', handle_help))
        application.add_handler(CommandHandler('flap', handle_flap))
        application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser('Control split flap display via Telegram bot.')
    parser.add_argument('--port', '-p', required=False, help='COM port; omit to list ports.')
    parser.add_argument('--token', '-t', required=False, help='Telegram bot token.')
    args = parser.parse_args()
    if args.port is None:
        list_ports()
    elif args.token is None:
        print('Specify a telegram bot token', file=sys.stderr)
        parser.print_help(file=sys.stderr)
        sys.exit(1)
    else:
        main(args.port, args.token)
