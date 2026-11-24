.. _yago2s:

yago2s
======

.. contents:: Table of Contents

Info
----

.. list-table::
   :header-rows: 1

   * -
     -
   * - Full Name
     - yago2s
   * - Direct download
     - `.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/yago2s.tar.gz>`_
   * - Source
     - `YAGO2s <https://yago-knowledge.org/downloads/yago-2s>`_


Graph Statistics
----------------

.. list-table::
   :header-rows: 1

   * - Num Nodes
     - Num Edges
   * - 25314540
     - 77869864


Edges Statistics
----------------

.. list-table::
   :header-rows: 1

   * - Edge Label
     - Num Edge Label
   * - linksTo
     - 38041748
   * - hasLongitude
     - 7466181
   * - hasLatitude
     - 7460415
   * - hasGeonamesEntityId
     - 7267069
   * - isPreferredMeaningOf
     - 2970027
   * - hasWikipediaArticleLength
     - 2886875
   * - hasWikipediaUrl
     - 2886312
   * - isLocatedIn
     - 1250704
   * - hasGender
     - 923364
   * - hasFamilyName
     - 838669
   * - hasGivenName
     - 827681
   * - wasBornOnDate
     - 805590
   * - wasCreatedOnDate
     - 722610
   * - isAffiliatedTo
     - 493085
   * - playsFor
     - 409703
   * - diedOnDate
     - 361932
   * - created
     - 277069
   * - hasNumberOfPeople
     - 230745
   * - hasWebsite
     - 226391
   * - wasBornIn
     - 189199
   * - hasArea
     - 129920
   * - actedIn
     - 127502
   * - hasWordnetDomain
     - 87104
   * - hasWonPrize
     - 72829
   * - hasGloss
     - 69598
   * - hasSynsetId
     - 68862
   * - hasDuration
     - 54741
   * - diedIn
     - 54171
   * - hasHeight
     - 50863
   * - isCitizenOf
     - 46015
   * - wasDestroyedOnDate
     - 43975
   * - directed
     - 41777
   * - hasPopulationDensity
     - 39408
   * - livesIn
     - 33610
   * - isConnectedTo
     - 33581
   * - hasMusicalRole
     - 32681
   * - graduatedFrom
     - 30388
   * - hasMotto
     - 27642
   * - happenedOnDate
     - 27408
   * - owns
     - 26540
   * - influences
     - 25819
   * - isMarriedTo
     - 25304
   * - wroteMusicFor
     - 24273
   * - hasWeight
     - 21256
   * - hasChild
     - 17320
   * - participatedIn
     - 16809
   * - hasPages
     - 15616
   * - happenedIn
     - 12500
   * - hasISBN
     - 10917
   * - isLeaderOf
     - 10695
   * - hasLength
     - 9010
   * - holdsPoliticalPosition
     - 6018
   * - edited
     - 5946
   * - hasAirportCode
     - 5714
   * - worksAt
     - 5134
   * - hasRevenue
     - 4114
   * - isPoliticianOf
     - 3751
   * - hasAcademicAdvisor
     - 3238
   * - hasThreeLetterLanguageCode
     - 2574
   * - hasCapital
     - 1937
   * - hasOfficialLanguage
     - 964
   * - dealsWith
     - 945
   * - hasBudget
     - 717
   * - hasGeonamesClassId
     - 672
   * - hasCurrency
     - 640
   * - exports
     - 579
   * - isKnownFor
     - 500
   * - isInterestedIn
     - 464
   * - imports
     - 391
   * - hasTLD
     - 270
   * - hasGDP
     - 241
   * - hasExport
     - 175
   * - hasExpenses
     - 174
   * - hasImport
     - 172
   * - hasLanguageCode
     - 156
   * - hasInflation
     - 155
   * - hasUnemployment
     - 145
   * - hasEconomicGrowth
     - 141
   * - hasGini
     - 130
   * - hasNumber
     - 104
   * - hasPoverty
     - 84
   * - hasConfidence
     - 80
   * - hasImdb
     - 9
   * - occursSince
     - 9
   * - startedOnDate
     - 9
   * - occursUntil
     - 7
   * - endedOnDate
     - 1
   * - hasNumberOfThings
     - 1


Queries
-------

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Language
   * - ``rpq/1``
     - ``isMarriedTo livesIn isLocatedIn isLocatedIn* dealsWith dealsWith*``
   * - ``rpq/2``
     - ``happenedIn hasCapital hasCapital* created created*``
   * - ``rpq/3``
     - ``happenedIn hasCapital hasCapital* owns owns*``
   * - ``rpq/4``
     - ``happenedIn hasCapital hasCapital* participatedIn participatedIn*``
   * - ``rpq/5``
     - ``happenedIn dealsWith dealsWith* hasCapital hasCapital*``
   * - ``rpq/6``
     - ``isCitizenOf hasCapital hasCapital* created created*``
   * - ``rpq/7``
     - ``isCitizenOf hasCapital hasCapital* owns owns*``
   * - ``rpq/8``
     - ``isCitizenOf hasCapital hasCapital* participatedIn participatedIn*``
   * - ``rpq/9``
     - ``isCitizenOf dealsWith dealsWith* hasCapital hasCapital*``
   * - ``rpq/10``
     - ``isLocatedIn hasCapital hasCapital* created created*``
   * - ``rpq/11``
     - ``isLocatedIn hasCapital hasCapital* owns owns*``
   * - ``rpq/12``
     - ``isLocatedIn dealsWith dealsWith* hasCapital hasCapital*``
   * - ``rpq/13``
     - ``isPoliticianOf hasCapital hasCapital* created created*``
   * - ``rpq/14``
     - ``isPoliticianOf hasCapital hasCapital* owns owns*``
   * - ``rpq/15``
     - ``isPoliticianOf hasCapital hasCapital* participatedIn participatedIn*``
   * - ``rpq/16``
     - ``wasBornIn hasCapital hasCapital* created created*``
   * - ``rpq/17``
     - ``wasBornIn hasCapital hasCapital* owns owns*``
   * - ``rpq/18``
     - ``wasBornIn hasCapital hasCapital* participatedIn participatedIn*``
   * - ``rpq/19``
     - ``wasBornIn dealsWith dealsWith* hasCapital hasCapital*``
   * - ``rpq/20``
     - ``created hasChild hasChild* isMarriedTo isMarriedTo*``
   * - ``rpq/21``
     - ``created influences influences* isMarriedTo isMarriedTo*``
   * - ``rpq/22``
     - ``created influences influences* hasChild hasChild*``
   * - ``rpq/23``
     - ``created isMarriedTo isMarriedTo* hasChild hasChild*``
   * - ``rpq/24``
     - ``hasChild influences influences* isMarriedTo isMarriedTo*``
   * - ``rpq/25``
     - ``hasChild influences influences* hasChild hasChild*``
   * - ``rpq/26``
     - ``hasChild isMarriedTo isMarriedTo* hasChild hasChild*``
   * - ``rpq/27``
     - ``hasChild hasChild hasChild* isMarriedTo isMarriedTo*``
   * - ``rpq/28``
     - ``influences hasChild hasChild* isMarriedTo isMarriedTo*``
   * - ``rpq/29``
     - ``influences isMarriedTo isMarriedTo* hasChild hasChild*``
   * - ``rpq/30``
     - ``influences influences influences* isMarriedTo isMarriedTo*``
   * - ``rpq/31``
     - ``influences influences influences* hasChild hasChild*``
   * - ``rpq/32``
     - ``isKnownFor hasChild hasChild* isMarriedTo isMarriedTo*``
   * - ``rpq/33``
     - ``isKnownFor isMarriedTo isMarriedTo* hasChild hasChild*``
   * - ``rpq/34``
     - ``isKnownFor influences influences* isMarriedTo isMarriedTo*``
   * - ``rpq/35``
     - ``isKnownFor influences influences* hasChild hasChild*``
   * - ``rpq/36``
     - ``isMarriedTo influences influences* isMarriedTo isMarriedTo*``
   * - ``rpq/37``
     - ``isMarriedTo influences influences* hasChild hasChild*``
   * - ``rpq/38``
     - ``isMarriedTo hasChild hasChild* isMarriedTo isMarriedTo*``
   * - ``rpq/39``
     - ``isMarriedTo isMarriedTo isMarriedTo* hasChild hasChild*``
