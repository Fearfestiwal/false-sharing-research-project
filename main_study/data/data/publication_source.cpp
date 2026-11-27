#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cpuid.h>
#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <random>
#include <set>
#include <thread>
#include <vector>
#include <string>

// Every object is owned by one worker. Volatile preserves observable stores;
// it is NOT a synchronization mechanism. Atomics only implement the start gate.
struct Job { std::string placement; std::vector<int> cpus; int batch,stride,rep; };
int main(int argc,char**argv){
 const uint64_t N=argc>1?std::stoull(argv[1]):16000000;
 const int reps=argc>2?std::stoi(argv[2]):9;
 DWORD bytes=0; GetLogicalProcessorInformationEx(RelationProcessorCore,nullptr,&bytes);
 std::vector<unsigned char> buf(bytes);
 if(!GetLogicalProcessorInformationEx(RelationProcessorCore,(PSYSTEM_LOGICAL_PROCESSOR_INFORMATION_EX)buf.data(),&bytes)) return 2;
 std::vector<int> physical,smt,efficient; std::ofstream topo("data/topology.csv");
 topo<<"core,cpu,core_type,efficiency_class,mask\n"; int core=0;
 auto original=SetThreadAffinityMask(GetCurrentThread(),1); if(!original)return 3;
 unsigned a,b,c,d; __cpuid(1,a,b,c,d); unsigned line=((b>>8)&255)*8;
 std::ofstream meta("data/environment.txt"); meta<<"N_per_thread="<<N<<"\nrepetitions="<<reps<<"\ncache_line_cpuid="<<line<<"\ncompiler="<<__VERSION__<<"\n";
 if(line!=64){std::cerr<<"This implementation requires 64-byte lines\n";return 4;}
 for(DWORD off=0;off<bytes;){auto p=(PSYSTEM_LOGICAL_PROCESSOR_INFORMATION_EX)(buf.data()+off);auto mask=p->Processor.GroupMask[0].Mask;
   bool first=true; for(int cpu=0;cpu<64;cpu++)if(mask&(1ull<<cpu)){
    if(!SetThreadAffinityMask(GetCurrentThread(),1ull<<cpu))return 5;
    unsigned x,y,z,w; __cpuid_count(0x1a,0,x,y,z,w);unsigned type=x>>24;
    topo<<core<<","<<cpu<<","<<type<<","<<(int)p->Processor.EfficiencyClass<<","<<mask<<"\n";
    if(type==0x40){smt.push_back(cpu);if(first)physical.push_back(cpu);}else if(type==0x20)efficient.push_back(cpu);
    first=false;
   }off+=p->Size;core++;
 }
 SetThreadAffinityMask(GetCurrentThread(),original);topo.close();
 std::vector<Job> jobs;
 auto add=[&](std::string name,std::vector<int> cpus,std::vector<int> counts){for(int t:counts)if(t<=(int)cpus.size())for(int batch:{1,16,256,(int)N})for(int stride:{8,64})for(int r=-1;r<reps;r++)jobs.push_back({name,std::vector<int>(cpus.begin(),cpus.begin()+t),batch,stride,r});};
 add("P_physical",physical,{1,2,4,6});add("P_SMT",smt,{2,4,8,12});add("E_physical",efficient,{1,2,4});
 if(jobs.empty())return 6;
 std::mt19937 rng(20261112);std::shuffle(jobs.begin(),jobs.end(),rng);
 std::stable_partition(jobs.begin(),jobs.end(),[](const Job& j){return j.rep<0;});
 std::ofstream raw("data/raw.csv");raw<<"order,placement,threads,batch,stride,rep,seconds,correct,affinity_ok,aligned_ok,updates_per_thread,storage_bytes\n";
 std::ofstream addr("data/addresses.csv");addr<<"order,thread,cpu,address,line_index,offset\n";
 int order=0;
 for(auto &j:jobs){
  int t=j.cpus.size();auto mem=(unsigned char*)_aligned_malloc(t*j.stride,64);if(!mem)return 7;
  for(int i=0;i<t;i++)*(uint64_t*)(mem+i*j.stride)=0;
  HANDLE finished=CreateEvent(nullptr,TRUE,FALSE,nullptr);
  std::atomic<int> ready{0},done{0},affok{1};std::atomic<bool> go{false};std::vector<std::thread> workers;
  for(int i=0;i<t;i++)workers.emplace_back([&,i]{
   if(!SetThreadAffinityMask(GetCurrentThread(),1ull<<j.cpus[i]))affok.store(0);
   volatile uint64_t* out=(volatile uint64_t*)(mem+i*j.stride);
   uint64_t x=i+1;ready.fetch_add(1);while(!go.load(std::memory_order_acquire))YieldProcessor();
   for(uint64_t start=0;start<N;start+=j.batch){uint64_t end=std::min(N,start+(uint64_t)j.batch);
    for(uint64_t k=start;k<end;k++)x=x*6364136223846793005ull+1442695040888963407ull;
    *out=x;
   }if(done.fetch_add(1,std::memory_order_acq_rel)==t-1)SetEvent(finished);
  });
  while(ready.load()!=t)std::this_thread::yield();auto begin=std::chrono::steady_clock::now();go.store(true,std::memory_order_release);
  WaitForSingleObject(finished,INFINITE);auto end=std::chrono::steady_clock::now();CloseHandle(finished);
  for(auto &w:workers)w.join();bool ok=true;
  for(int i=0;i<t;i++){uint64_t x=i+1;for(uint64_t k=0;k<N;k++)x=x*6364136223846793005ull+1442695040888963407ull;if(*(uint64_t*)(mem+i*j.stride)!=x)ok=false;
   uintptr_t p=(uintptr_t)(mem+i*j.stride);addr<<order<<","<<i<<","<<j.cpus[i]<<","<<p<<","<<p/64<<","<<p%64<<"\n";
  }
  bool aligned=((uintptr_t)mem%64)==0;
  raw<<order<<","<<j.placement<<","<<t<<","<<j.batch<<","<<j.stride<<","<<j.rep<<","<<std::chrono::duration<double>(end-begin).count()<<","<<ok<<","<<affok.load()<<","<<aligned<<","<<(N+j.batch-1)/j.batch<<","<<t*j.stride<<"\n";raw.flush();
  _aligned_free(mem);if(!ok||!affok||!aligned)return 8;
  if(++order%40==0)std::cout<<order<<"/"<<jobs.size()<<std::endl;
 }
}
