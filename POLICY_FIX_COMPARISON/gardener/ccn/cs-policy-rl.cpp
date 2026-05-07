/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/*
 * Copyright (c) 2014-2019,  Regents of the University of California,
 *                           Arizona Board of Regents,
 *                           Colorado State University,
 *                           University Pierre & Marie Curie, Sorbonne University,
 *                           Washington University in St. Louis,
 *                           Beijing Institute of Technology,
 *                           The University of Memphis.
 *
 * This file is part of NFD (Named Data Networking Forwarding Daemon).
 * See AUTHORS.md for complete list of NFD authors and contributors.
 *
 * NFD is free software: you can redistribute it and/or modify it under the terms
 * of the GNU General Public License as published by the Free Software Foundation,
 * either version 3 of the License, or (at your option) any later version.
 *
 * NFD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
 * without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
 * PURPOSE.  See the GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License along with
 * NFD, e.g., in COPYING.md file.  If not, see <http://www.gnu.org/licenses/>.
 */

#include "cs-policy-rl.hpp"
#include "cs.hpp"
#include <iostream>
#include <fstream>

namespace nfd {
namespace cs {
namespace rl {

const std::string RLPolicy::POLICY_NAME = "rl";
NFD_REGISTER_CS_POLICY(RLPolicy);

RLPolicy::RLPolicy()
  : Policy(POLICY_NAME)
{
    std::ofstream outfile ("/ndnSIM/ns-3/src/ndnSIM/NFD/daemon/table/framework/cache.pkl");
    std::ofstream outfile2 ("/ndnSIM/ns-3/src/ndnSIM/NFD/daemon/table/framework/clingo.pkl");
    std::ofstream outfile3 ("/ndnSIM/ns-3/src/ndnSIM/NFD/daemon/table/framework/cache.txt");
    outfile.close();
    outfile2.close();
    outfile3.close();
}

// i is added to the cache
void
RLPolicy::doAfterInsert(EntryRef i)
{
  this->insertToQueue(i, true);
  this->evictEntries();
}

void
RLPolicy::doAfterRefresh(EntryRef i)
{
  this->insertToQueue(i, false);
}

void
RLPolicy::doBeforeErase(EntryRef i)
{
  std::cout << "erase";
  m_queue.get<1>().erase(i);
}

void
RLPolicy::doBeforeUse(EntryRef i)
{
  this->insertToQueue(i, false);
}

void
RLPolicy::evictEntries()
{
    if (this->getCs()->size() > this->getLimit()) {
        //std::cout << "This should never happen!";
    }
}

void
RLPolicy::insertToQueue(EntryRef i, bool isNewEntry)
{

  // run the python script and evict the resulting cache entry saved to cache.txt
  BOOST_ASSERT(this->getCs() != nullptr);
  std::ostringstream oss;
  oss << i->getName();
  std::string name = oss.str();
  std::string command = "python3 src/ndnSIM/NFD/daemon/table/framework/run.py \"";
  command += name;
  command += "\"";
  int result = system(command.c_str());
  std::ifstream file("src/ndnSIM/NFD/daemon/table/framework/cache.txt");
    std::string str;
    std::getline(file, str);
  file.close();
  if (!str.empty()){

      BOOST_ASSERT(!m_queue.empty());
      auto it = m_queue.begin();
      int remove = 0;
      int count = 0;
      for(EntryRef ref: m_queue) {
        if (ref->getName() == str){
        remove = count;
        }
        count = count + 1;
  }

      std::advance(it, remove);

      EntryRef j = *it;
      m_queue.erase(it);



    this->emitSignal(beforeEvict, j);
  }
  m_queue.push_back(i);

}

} // namespace rl
} // namespace cs
} // namespace nfd
