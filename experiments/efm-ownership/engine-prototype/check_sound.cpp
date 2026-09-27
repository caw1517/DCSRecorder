// Verify the observation wrapper forwards parameters unchanged and exports correctly.
#include <windows.h>
#include <filesystem>
#include <iostream>
#include <stdexcept>
int main(int argc,char** argv) {
    try {
        if(argc!=2)throw std::runtime_error("provide isolated sound-probe DLL");
        auto dll=LoadLibraryW(std::filesystem::absolute(argv[1]).c_str());
        if(!dll)throw std::runtime_error("DLL load failed");
        using Getter=double(*)(unsigned);
        auto original=reinterpret_cast<Getter>(GetProcAddress(dll,"engine_sample_get_param"));
        auto wrapped=reinterpret_cast<Getter>(GetProcAddress(dll,"ed_fm_get_param"));
        if(!original || !wrapped)throw std::runtime_error("getter export missing");
        for(unsigned index: {0u,1u,100u,101u,102u,103u,104u,105u,112u,114u,128u,200u,201u,202u,203u,204u,205u,212u,214u,228u,2000u,10000u})
            for(int i=0;i<3;++i)if(wrapped(index)!=original(index))throw std::runtime_error("parameter changed");
        FreeLibrary(dll);
        std::cout<<"PASS: sound observation forwards all 66 getter calls unchanged\n";
        return 0;
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
