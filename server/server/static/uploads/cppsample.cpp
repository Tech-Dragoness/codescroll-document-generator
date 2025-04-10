#include <iostream>
using namespace std;

int main() {
    int level = 2;

    switch(level) {
        case 1:
            cout << "🧙 Apprentice level." << endl;
            break;
        case 2:
            cout << "🧝 Intermediate mage." << endl;
            break;
        case 3:
            cout << "🐉 Dragon Master!" << endl;
            break;
        default:
            cout << "🌌 Unknown level of magic." << endl;
    }

    return 0;
}
