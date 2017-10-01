from bs4 import BeautifulSoup
import requests
import re
import sys

reload(sys)
sys.setdefaultencoding('utf8')

class QuinielaScrapper:
    """Web scrapper to get 4chan thread messages"""

    # https://resultados.as.com/quiniela/2017_2018/jornada_10/

    def __init__(self):
        """Creates the scraper
        """
        self.url = "https://resultados.as.com/quiniela/2017_2018/"
        self.scraper = None

    def is_journey_available(self, journey):
        journey_url = self.url + "jornada_" + str(journey)
        quiniela_page = requests.get(journey_url)
        quiniela_page_text = quiniela_page.text
        self.scraper = BeautifulSoup(quiniela_page_text, "lxml")

        return len(self.scraper.select('div.p404')) == 0


    def get_journey(self, journey):
        partidos = []

        journey_url = self.url + "jornada_" + str(journey)
        print "try with: %s" % journey_url
        quiniela_page = requests.get(journey_url)
        quiniela_page_text = quiniela_page.text
        self.scraper = BeautifulSoup(quiniela_page_text, "lxml") 
        cont_partidos = self.scraper.select('div.cont-partido')

        # Loop through each match and retrieve results
        for cont_partido in cont_partidos:
            num = cont_partido.select('span.pos')[0].text
            local, visitante, pronostico = "", "", ""

            if num == "15.":
                local = cont_partido.select('a.visitante')[0].select('span.nombre-equipo')[0].text
                visitante = cont_partido.select('a.visitante')[1].select('span.nombre-equipo')[0].text
                pronostico1, pronostico2 = "", ""
                try:
                    pronostico1 = cont_partido.select('span.finalizado')[0].text
                    pronostico2 = cont_partido.select('span.finalizado')[1].text
                except IndexError:
                    pass
                pronostico = "%s - %s" % (pronostico1, pronostico2)
            else:
                local = cont_partido.select('a.local')[0].select('span.nombre-equipo')[0].text
                visitante = cont_partido.select('a.visitante')[0].select('span.nombre-equipo')[0].text
                try:
                    pronostico = cont_partido.select('span.cont-pronosticos')[0].select('span.finalizado')[0].text
                except IndexError:
                    pass

            print "%s %s - %s: %s" % (num, local, visitante, pronostico)
            partidos.append({
                "match": "%s - %s" % (local, visitante),
                "result": pronostico
            })

        return partidos


    def getFirstAtBoard(self, board):
        """Gets OP's message of first thread in the board

        :board: board where we'll get the thread

        :return: {'img': opPostImg,
               'title': opPostTitle, 
               'msg': opPostMsg,
               'no': opPostNo,
               'noLink': opPostNoLink}
        """
        print 'Getting in the scraper'
        fourChanBoard = requests.get(self.url + board)
        print 'Im done with request'
        fourChanBoard = fourChanBoard.text
        self.scraper = BeautifulSoup(fourChanBoard, "lxml") 
        print 'Scrapper retrieved!'

        board_ = self.scraper.select('div.board')[0]
        opPost = board_.select('div.opContainer')[2].select('div.op')[0]
        opPostMsg = str(opPost.select('blockquote.postMessage')[0])
        opPostImg = opPost.select('img')[0]['src'][2:]

        # Remove HTML tags
        lineBreaker = re.compile(r'<br/>')
        opPostMsg = lineBreaker.sub('\n', opPostMsg)
        tagBreaker = re.compile(r'<.*?>')
        opPostMsg = tagBreaker.sub('', opPostMsg)

        opPostInfo = opPost.select('div.postInfo')[0]
        opPostTitle = opPostInfo.select('span.subject')[0].text
        opPostNo = opPostInfo.select('span.postNum')[0].select('a')[0]['href']
        print opPostNo
        opPostNoLink = self.boardsURL + board + '/' + opPostNo
        opPostNo = opPostNo.split('#')[1]

        return {'img': opPostImg,
               'title': opPostTitle, 
               'msg': opPostMsg,
               'no': opPostNo,
               'noLink': opPostNoLink}
            

if __name__ == '__main__':
    scrapper = QuinielaScrapper()
    scrapper.get_journey(10)


