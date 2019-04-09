import base64
import urllib3
import asyncio
import aiohttp
urllib3.disable_warnings()


class Action:

    def __init__(self, actorCellId, championId, completed, id, type, pickTurn=None):
        self.actor_cell_id = actorCellId
        self.champion_id = championId
        self.completed = completed
        self.id = id
        self.type = type
        self.pick_turn = pickTurn

    def to_json(self):
        if self.completed is False:
            completed = 'false'
        else:
            completed = 'true'
        json = f'"actorCellId": {self.actor_cell_id}, "championId": {self.champion_id}, "completed": {completed},' \
               f' "id": {self.id}, "type": "{self.type}"'
        if self.pick_turn:
            json = json + f',"pickTurn": {self.pick_turn}'
        return '{' + json + '}'


class SummonerInSelection:

    def __init__(self, assignedPosition, cellId, championId, championPickIntent, entitledFeatureType, playerType,
                 selectedSkinId, spell1Id, spell2Id, summonerId, team, wardSkinId):
        self.assigned_position = assignedPosition
        self.cell_id = cellId
        self.champion_id = championId
        self.champion_pick_intent = championPickIntent
        self.entitled_feature_type = entitledFeatureType
        self.player_type = playerType
        self.selected_skin_id = selectedSkinId
        self.spell_id_1 = spell1Id
        self.spell_id_2 = spell2Id
        self.summoner_id = summonerId
        self.team = team
        self.ward_skin_id = wardSkinId


class Summoner:

    def __init__(self, accountId, displayName, internalName, percentCompleteForNextLevel, profileIconId, puuid,
                 summonerId, summonerLevel):
        self.account_id = accountId
        self.display_name = displayName
        self.internal_name = internalName
        self.percent_complete_for_next_level = percentCompleteForNextLevel
        self.profile_icon_id = profileIconId
        self.puuid = puuid
        self.summoner_id = summonerId
        self.summoner_level = summonerLevel


class Client:

    def __init__(self, process, pid, port, password, protocol, loop, champion_id):
        self.champion_id = champion_id
        self.url = f'{protocol}://127.0.0.1:{port}'
        self.process = process
        self.pid = pid
        self.password = password
        self.session = None
        self.summoner = None
        self.loop = loop
        self.is_first_time = True
        self.headers = {"Authorization": "Basic " + base64.b64encode(f"riot:{self.password}".encode('utf-8'))
                        .decode('utf-8'), "Accept": "application/json"}

    async def setup(self, session):
        print({"Authorization": "Basic " + base64.b64encode(f"riot:{self.password}".encode('utf-8')).decode('utf-8')})
        self.summoner = await self._get_summoner_info(session)
        print(self.summoner.summoner_id)

    async def send_get_request(self, session, url, **kwargs):
        async with session.get(self.url+url, **kwargs) as response:
            return await response.json()

    async def send_patch_request(self, session, url, **kwargs):
        async with session.patch(self.url + url, **kwargs) as response:
            await response.json()
            return response.status

    async def send_post_request(self, session, url):
        async with session.post(self.url + url) as response:
            await response.json()
            return response.status

    async def _get_summoner_info(self, session):
        response = await self.send_get_request(session, '/lol-summoner/v1/current-summoner')
        if response:
            del response['rerollPoints']
            del response['xpSinceLastLevel']
            del response['xpUntilNextLevel']
            summoner = Summoner(**response)
            return summoner

    async def _get_champ_selection_actions(self, session):
        response = await self.send_get_request(session, '/lol-champ-select/v1/session')
        if response:
            my_team = response['myTeam']
            actions = response['actions']
            return my_team, actions

    async def ban(self, session, champion_id_to_ban):
        cell_id,  actions = await self._get_cell_id_and_actions(session)
        for action in actions:
            if action.type == 'ban' and action.actor_cell_id == cell_id:
                action.champion_id = champion_id_to_ban
                res = await self.send_patch_request(session, f'/lol-champ-select/v1/session/actions/{action.id}', data=action.to_json()
                                                    , headers={"Content-Type": "application/json"})
                if res == 204:
                    res = await self.send_post_request(session, f'/lol-champ-select/v1/session/actions/{action.id}/complete')
                if res == 204:
                    return True
                print('something failed')

    async def _get_cell_id_and_actions(self, session):
        team, list_of_actions = await self._get_champ_selection_actions(session)
        list_actions = []
        for actions in list_of_actions:
            for action in actions:
                list_actions.append(Action(**action))
        for mate in team:
            summoner = SummonerInSelection(**mate)
            if summoner.summoner_id == self.summoner.summoner_id:
                return summoner.cell_id, list_actions

    async def _check_game_phase(self, session):
        response = await self.send_get_request(session, '/lol-gameflow/v1/gameflow-phase')
        print(response)
        if response == "ChampSelect":
            print('Do something')
            await asyncio.sleep(20)
            print('sleep done')
            ban = await self.ban(session, self.champion_id)
            if ban is True:
                print('Ban complete')
                self.__del__()
                self.loop.close()
                exit()

    async def __call__(self):
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False), headers=self.headers) as session:
            if self.is_first_time:
                await self.setup(session)
                self.is_first_time = False
            await self._check_game_phase(session)

    def __del__(self):
        self.session.close()


