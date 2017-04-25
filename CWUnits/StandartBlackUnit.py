# -*- coding: utf-8 -*-
from CWUnits.BaseUnit import *
from telethon import TelegramClient
from telethon.tl.functions.messages import GetInlineBotResultsRequest, SendInlineBotResultRequest, ForwardMessageRequest
from telethon.utils import get_input_peer
import telethon.helpers as utils
from enums import *
from time import sleep
from random import randint
from Character import Character
from telethon.tl.types import UpdateShortChatMessage, UpdateShortMessage, UpdatesTg, UpdateNewChannelMessage, \
    UpdateNewMessage, Message
import re
import regexp


class Module(BaseUnit):
    def __init__(self, tg_client: TelegramClient, character: Character):
        super().__init__(tg_client, character)

    def _send_captcha(self, captcha):
        sleep(randint(5, 10))
        self._append_to_send_queue(self._cwBot, captcha)

    def _send_order(self, order):
        self._lock.acquire()
        if order[0] == CharacterAction.ATTACK:
            result = self._tgClient.invoke(
                GetInlineBotResultsRequest(get_input_peer(self._orderBot),
                                           get_input_peer(self._cwBot),
                                           '', ''))
            res = self._find_inline_by_title(result.results, 'Атака')
            self._tgClient.invoke(
                SendInlineBotResultRequest(get_input_peer(self._cwBot),
                                           utils.generate_random_long(),
                                           result.query_id, res.id))
            sleep(randint(2, 5))
            self._send_castle(order[1])
        elif order[0] == CharacterAction.DEFENCE:
            result = self._tgClient.invoke(
                GetInlineBotResultsRequest(get_input_peer(self._orderBot),
                                           get_input_peer(self._cwBot),
                                           '', ''))
            res = self._find_inline_by_title(result.results, 'Защита')
            self._tgClient.invoke(
                SendInlineBotResultRequest(get_input_peer(self._cwBot),
                                           utils.generate_random_long(),
                                           result.query_id, res.id))
            sleep(randint(2, 5))
            self._send_castle(order[1])
        elif order[0] == CharacterAction.QUEST:
            self._append_to_send_queue(self._cwBot, Buttons.QUEST.value)
            sleep(randint(2, 5))
            self._append_to_send_queue(self._cwBot, order[1].value)
        elif order[0] == CharacterAction.CAPTCHA:
            self._append_to_send_queue(self._captchaBot, order[1])
            sleep(28)
        elif order[0] == CharacterAction.GET_DATA:
            self._append_to_send_queue(self._cwBot, order[1].value)
        self._lock.release()

    def _send_castle(self, castle):
        result = self._tgClient.invoke(
            GetInlineBotResultsRequest(get_input_peer(self._orderBot),
                                       get_input_peer(self._cwBot),
                                       '', ''))
        res = result.results[0]
        if castle == Castle.BLACK:
            res = self._find_inline_by_title(result.results, 'Черный замок')
        elif castle == Castle.BLUE:
            res = self._find_inline_by_title(result.results, 'Синий замок')
        elif castle == Castle.RED:
            res = self._find_inline_by_title(result.results, 'Красный замок')
        elif castle == Castle.YELLOW:
            res = self._find_inline_by_title(result.results, 'Желтый замок')
        elif castle == Castle.WHITE:
            res = self._find_inline_by_title(result.results, 'Белый замок')
        elif castle == Castle.LES:
            res = self._find_inline_by_title(result.results, 'Лесной форт')
        elif castle == Castle.GORY:
            res = self._find_inline_by_title(result.results, 'Горный форт')
        self._tgClient.invoke(
            SendInlineBotResultRequest(get_input_peer(self._cwBot),
                                       utils.generate_random_long(),
                                       result.query_id, res.id))

    @staticmethod
    def _find_inline_by_title(inline_results, title):
        for res in inline_results:
            if res.title == title:
                return res

    def _action(self):
        self._send_order(self._character.ask_action())

    def _receive(self, msg):
        if type(msg) is UpdatesTg:
            for upd in msg.updates:
                if type(upd) is UpdateNewChannelMessage:
                    message = upd.message
                    if type(message) is Message:
                        channel = None
                        for chat in msg.chats:
                            if chat.id == message.to_id.channel_id:
                                channel = chat
                        if message.out:
                            pass
                        else:
                            if channel and self._channel_in_list(channel):
                                if self._can_order_id(message.from_id):
                                    self._character.set_order(message.message)
                elif type(upd) is UpdateNewMessage:
                    message = upd.message
                    if type(message) is Message:
                        if message.out:
                            if message.to_id.user_id == message.from_id:
                                self._character.set_order(message.message)
                        elif self._id_in_list(message.from_id):
                            if self._can_order_id(message.from_id):
                                print('Получли приказ')
                                self._character.set_order(message.message)
                            elif message.from_id == self._cwBot.id:
                                print('Получили сообщение от ChatWars')
                                if re.search(regexp.main_hero, message.message):
                                    self._lock.acquire()
                                    self._tgClient.invoke(ForwardMessageRequest(get_input_peer(self._dataBot),
                                                                                message.id,
                                                                                utils.generate_random_long()))
                                    self._lock.release()
                                self._character.parse_message(message.message)
                            elif message.from_id == self._captchaBot.id:
                                print('Получили сообщение от капчебота, пересылаем в ChatWars')
                                self._send_captcha(message.message)
        elif type(msg) is UpdateShortMessage:
            if msg.out:
                print('You sent {} to user #{}'.format(msg.message,
                                                       msg.user_id))
            elif self._id_in_list(msg.user_id):
                if self._can_order_id(msg.user_id):
                    print('Получли приказ')
                    self._character.set_order(msg.message)
                elif msg.user_id == self._cwBot.id:
                    print('Получили сообщение от ChatWars')
                    self._character.parse_message(msg.message)
                elif msg.user_id == self._captchaBot.id:
                    print('Получили сообщение от капчебота, пересылаем в ChatWars')
                    self._send_captcha(msg.message)

        elif type(msg) is UpdateShortChatMessage:
            if msg.out:
                print('You sent {} to chat #{}'.format(msg.message,
                                                       msg.chat_id))
            elif self._id_in_list(msg.from_id):
                print('[Chat #{}, user #{} sent {}]'.format(
                    msg.chat_id, msg.from_id,
                    msg.message))